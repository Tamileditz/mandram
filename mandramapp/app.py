from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif'}

def get_db_connection():
    try:
        conn = sqlite3.connect('database.db', check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def authenticate(username, password):
    conn = get_db_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

def insert_member(name, dob, address, phone, referred_by, occupation, date_of_join, status, photo_url):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO members (name, dob, address, phone, referred_by, occupation, date_of_join, status, photo_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, dob, address, phone, referred_by, occupation, date_of_join, status, photo_url))
    conn.commit()
    conn.close()

def get_member_details(member_id=None, name=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM members WHERE 1=1'
    params = []
    
    if member_id:
        query += ' AND id = ?'
        params.append(member_id)
        
    if name:
        query += ' AND name LIKE ?'
        params.append(f'%{name}%')
        
    cursor.execute(query, params)
    data = cursor.fetchall()
    conn.close()
    return data

def update_member(member_id, name, dob, address, phone, referred_by, occupation, date_of_join, status, photo_url):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE members
        SET name = ?, dob = ?, address = ?, phone = ?, referred_by = ?, occupation = ?, date_of_join = ?, status = ?, photo_url = ?
        WHERE id = ?
    ''', (name, dob, address, phone, referred_by, occupation, date_of_join, status, photo_url, member_id))
    conn.commit()
    conn.close()

# Functions for handling events
def insert_event(title, date, description, image_url):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO events (title, date, description, image_url)
        VALUES (?, ?, ?, ?)
    ''', (title, date, description, image_url))
    conn.commit()
    conn.close()

def get_events():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM events')
    events = cursor.fetchall()
    conn.close()
    return events

def get_event_details(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM events WHERE id = ?', (event_id,))
    event = cursor.fetchone()
    conn.close()
    return event

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = authenticate(username, password)
        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/data-entry', methods=['GET', 'POST'])
def data_entry():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        address = request.form['address']
        phone = request.form['phone']
        referred_by = request.form['referred_by']
        occupation = request.form['occupation']
        date_of_join = request.form['date_of_join']
        status = request.form['status']
        
        # Handle file upload
        file = request.files.get('image')
        if file and allowed_file(file.filename):
            filename = f"{name}_{file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            photo_url = filename  # Save just the filename in the database
        else:
            photo_url = None
        
        insert_member(name, dob, address, phone, referred_by, occupation, date_of_join, status, photo_url)
        flash('Member details added successfully', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('data_entry.html', username=session['username'])

@app.route('/view-edit', methods=['GET', 'POST'])
def view_edit():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        search_id = request.form.get('search_id')
        search_name = request.form.get('search_name')
        members = get_member_details(member_id=search_id, name=search_name)
        return render_template('view_edit.html', members=members, username=session['username'])
    
    return render_template('view_edit.html', members=None, username=session['username'])

@app.route('/edit-member/<int:member_id>', methods=['GET', 'POST'])
def edit_member(member_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        address = request.form['address']
        phone = request.form['phone']
        referred_by = request.form['referred_by']
        occupation = request.form['occupation']
        date_of_join = request.form['date_of_join']
        status = request.form['status']
        
        # Handle file upload
        file = request.files.get('image')
        if file and allowed_file(file.filename):
            filename = f"{member_id}_{file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            photo_url = filename  # Save just the filename in the database
        else:
            # Retain old photo URL if no new file is uploaded
            cursor.execute('SELECT photo_url FROM members WHERE id = ?', (member_id,))
            photo_url = cursor.fetchone()['photo_url']
        
        update_member(member_id, name, dob, address, phone, referred_by, occupation, date_of_join, status, photo_url)
        flash('Member details updated successfully', 'success')
        return redirect(url_for('view_edit'))
    
    cursor.execute('SELECT * FROM members WHERE id = ?', (member_id,))
    member = cursor.fetchone()
    conn.close()

    return render_template('edit_member.html', member=member, username=session['username'])




@app.route('/member-detail/<int:member_id>', methods=['GET'])
def member_detail(member_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    member = get_member_details(member_id=member_id)
    
    if not member:
        flash('Member not found', 'error')
        return redirect(url_for('view_edit'))
    
    return render_template('member_detail.html', member=member[0], username=session['username'])

# Routes for events
@app.route('/create-event', methods=['GET', 'POST'])
def create_event():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        date = request.form['date']
        description = request.form['description']
        
        file = request.files.get('image')
        if file and allowed_file(file.filename):
            filename = f"{title}_{file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_url = filename
        else:
            image_url = None
        
        insert_event(title, date, description, image_url)
        flash('Event created successfully', 'success')
        return redirect(url_for('view_event'))
    
    return render_template('create_event.html', username=session['username'])

@app.route('/view-event')
def view_event():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    events = get_events()
    return render_template('view_event.html', events=events, username=session['username'])

@app.route('/event-detail/<int:event_id>')
def event_detail(event_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    event = get_event_details(event_id)
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('view_event'))
    
    return render_template('event_detail.html', event=event, username=session['username'])

# Route for serving uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/delete-event/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First, get the event details to know if an image exists
    cursor.execute('SELECT image_url FROM events WHERE id = ?', (event_id,))
    event = cursor.fetchone()
    
    if event:
        # Delete the event from the database
        cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
        conn.commit()
        
        # If there was an image, remove it from the filesystem
        image_url = event['image_url']
        if image_url:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], image_url)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        flash('Event deleted successfully', 'success')
    else:
        flash('Event not found', 'error')
    
    conn.close()
    return redirect(url_for('view_event'))



# Run the app with proper settings
if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(host="0.0.0.0", port=int(os.getenv('PORT', 5000)))
    app.run(debug=True)




