import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from tinydb import TinyDB, Query
from Crypto.Hash import MD5
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from functools import wraps
import base64
import json
import requests as http_requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'gov_secure_key_2024')

db = TinyDB('data/database.json')
users_table = db.table('users')
documents_table = db.table('documents')
messages_table = db.table('messages')
orders_table = db.table('orders')
notifications_table = db.table('notifications')

UPLOAD_FOLDER = 'uploads'
ENCRYPTED_FOLDER = 'uploads/encrypted'
DECRYPTED_FOLDER = 'uploads/decrypted'

ENCRYPTION_KEY = b'GovernmentKey123'

def md5_hash(text):
    h = MD5.new()
    h.update(text.encode('utf-8'))
    return h.hexdigest()

def encrypt_file(data):
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data, AES.block_size))
    iv = base64.b64encode(cipher.iv).decode('utf-8')
    ct = base64.b64encode(ct_bytes).decode('utf-8')
    return iv, ct

def decrypt_file(iv, ct):
    iv = base64.b64decode(iv)
    ct = base64.b64decode(ct)
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct), AES.block_size)
    return pt

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] != role:
                flash('You do not have permission to access this page', 'error')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

TURNSTILE_SECRET_KEY = "0x4AAAAAACuiSnb1IPwlx_hGLAvErZHcdr0" 

def verify_turnstile(token: str) -> bool:
    """Verify a Cloudflare Turnstile token server-side."""
    if not token:
        return False
    try:
        resp = http_requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={
                "secret": TURNSTILE_SECRET_KEY,
                "response": token,
            },
            timeout=5,
        )
        result = resp.json()
        return result.get("success", False)
    except Exception as e:
        return False
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        full_name = request.form['full_name']
        role = request.form['role']
        department = request.form.get('department', '')
        phone = request.form.get('phone', '')
        address = request.form.get('address', '')
        
        User = Query()
        if users_table.search(User.username == username):
            flash('Username already exists', 'error')
            return redirect(url_for('signup'))
        
        hashed_password = md5_hash(password)
        
        users_table.insert({
            'username': username,
            'password': hashed_password,
            'email': email,
            'full_name': full_name,
            'role': role,
            'department': department,
            'phone': phone,
            'address': address,
            'created_at': datetime.now().isoformat()
        })
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # ── Turnstile verification ──────────────────────────────────────
        turnstile_token = request.form.get('cf-turnstile-response', '')
        if not verify_turnstile(turnstile_token):
            return render_template(
                'login.html',
                turnstile_error=True,
                error="Human verification failed. Please try again."
            )
        # ───────────────────────────────────────────────────────────────

        User = Query()
        user = users_table.search(User.username == username)
        
        if user and user[0]['password'] == md5_hash(password):
            session['user_id'] = user[0].doc_id
            session['username'] = user[0]['username']
            session['role'] = user[0]['role']
            session['full_name'] = user[0]['full_name']
            
            if user[0]['role'] == 'government':
                return redirect(url_for('government_dashboard'))
            elif user[0]['role'] == 'collector':
                return redirect(url_for('collector_dashboard'))
            else:
                return redirect(url_for('localbody_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

@app.route('/government/dashboard')
@login_required
@role_required('government')
# AFTER
def government_dashboard():
    User = Query()
    Order = Query()
    Document = Query()
    Notification = Query()

    active_orders    = orders_table.search(Order.status == 'active')
    total_users      = users_table.search(
        (User.role == 'collector') | (User.role == 'localbody')
    )
    total_documents  = documents_table.all()
    pending_reports  = notifications_table.search(
        (Notification.target_role == 'government') & (Notification.read == False)
    )

    return render_template('government/dashboard.html',
        active_orders=len(active_orders),
        total_users=len(total_users),
        total_documents=len(total_documents),
        pending_reports=len(pending_reports)
    )

@app.route('/government/issue-order', methods=['GET', 'POST'])
@login_required
@role_required('government')
def government_issue_order():
    if request.method == 'POST':
        order_title = request.form['order_title']
        order_content = request.form['order_content']
        priority = request.form['priority']
        target_roles = request.form.getlist('target_roles')
        
        orders_table.insert({
            'title': order_title,
            'content': order_content,
            'priority': priority,
            'target_roles': target_roles,
            'issued_by': session['username'],
            'issued_at': datetime.now().isoformat(),
            'status': 'active'
        })
        
        for role in target_roles:
            notifications_table.insert({
                'target_role': role,
                'message': f"New Government Order: {order_title}",
                'from_user': session['username'],
                'created_at': datetime.now().isoformat(),
                'read': False
            })
        
        flash('Government Order issued successfully', 'success')
    
    orders = orders_table.all()
    return render_template('government/issue_order.html', orders=orders)

@app.route('/government/manage-users')
@login_required
@role_required('government')
def government_manage_users():
    User = Query()
    collectors = users_table.search(User.role == 'collector')
    localbodies = users_table.search(User.role == 'localbody')
    return render_template('government/manage_users.html', collectors=collectors, localbodies=localbodies)

@app.route('/government/share-data', methods=['GET', 'POST'])
@login_required
@role_required('government')
def government_share_data():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        share_with = request.form.getlist('share_with')
        
        documents_table.insert({
            'title': title,
            'content': content,
            'shared_with': share_with,
            'uploaded_by': session['username'],
            'role': 'government',
            'created_at': datetime.now().isoformat(),
            'type': 'shared_data'
        })
        
        flash('Data shared successfully', 'success')
    
    Document = Query()
    shared_docs = documents_table.search(Document.role == 'government')
    return render_template('government/share_data.html', documents=shared_docs)


@app.route('/government/view-reports')
@login_required
@role_required('government')
def government_view_reports():
    User = Query()
    Document = Query()
    Order = Query()

    total_collectors  = len(users_table.search(User.role == 'collector'))
    total_localbodies = len(users_table.search(User.role == 'localbody'))
    total_documents   = len(documents_table.all())
    total_orders      = len(orders_table.search(Order.status == 'active'))

    reports = documents_table.search(Document.type == 'report')

    return render_template('government/view_reports.html',
        total_collectors=total_collectors,
        total_localbodies=total_localbodies,
        total_documents=total_documents,
        total_orders=total_orders,
        reports=reports
    )
    User = Query()
    Document = Query()
    Order = Query()
    total_collectors = len(users_table.search(User.role == 'collector'))
    total_localbodies = len(users_table.search(User.role == 'localbody'))
    total_orders = len(orders_table.all())
    total_documents = len(documents_table.all())
    
    reports = documents_table.search(Document.type == 'report')
    
    return render_template('government/view_reports.html', 
                         total_collectors=total_collectors,
                         total_localbodies=total_localbodies,
                         total_orders=total_orders,
                         total_documents=total_documents)

@app.route('/government/notifications')
@login_required
@role_required('government')
def government_notifications():
    Notification = Query()
    notifications = notifications_table.search(Notification.target_role == 'government')
    for n in notifications:
        if 'read' not in n:
            notifications_table.update({'read': False}, doc_ids=[n.doc_id])
            n['read'] = False
        n['id'] = n.doc_id
    return render_template('government/notifications.html', notifications=notifications)

@app.route('/government/notifications/mark-read/<int:notif_id>', methods=['POST'])
@login_required
@role_required('government')
def government_mark_notification_read(notif_id):
    notifications_table.update({'read': True}, doc_ids=[notif_id])
    return redirect(url_for('government_notifications'))
@app.route('/government/notifications/mark-all-read', methods=['POST'])
@login_required
@role_required('government')
def government_mark_all_notifications_read():
    Notification = Query()
    notifications_table.update({'read': True}, Notification.target_role == 'government')
    return redirect(url_for('government_notifications'))

@app.route('/collector/dashboard')
@login_required
@role_required('collector')
def collector_dashboard():
    Document = Query()
    Order = Query()
    Notification = Query()
    username = session.get('username')

    pending_orders = orders_table.search(Order.target_roles.any(['collector']))
    uploaded_files = documents_table.search(
        (Document.uploaded_by == username) & (Document.type == 'encrypted_file')
    )
    shared_docs = documents_table.search(
        (Document.uploaded_by == username) & (Document.type == 'shared_data')
    )
    notifications = notifications_table.search(
        (Notification.target_role == 'collector') & (Notification.read == False)
    )

    return render_template('collector/dashboard.html',
        pending_orders=len(pending_orders),
        files_uploaded=len(uploaded_files),
        docs_shared=len(shared_docs),
        new_notifications=len(notifications)
    )

@app.route('/collector/upload-file', methods=['GET', 'POST'])
@login_required
@role_required('collector')
def collector_upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file_data = file.read()
        file_hash = md5_hash(base64.b64encode(file_data).decode('utf-8'))
        iv, encrypted_data = encrypt_file(file_data)
        
        encrypted_filename = f"enc_{file_hash}_{file.filename}"
        encrypted_path = os.path.join(ENCRYPTED_FOLDER, encrypted_filename)
        
        with open(encrypted_path, 'w') as f:
            json.dump({'iv': iv, 'data': encrypted_data, 'original_filename': file.filename}, f)
        
        documents_table.insert({
            'title': request.form.get('title', file.filename),
            'description': request.form.get('description', ''),
            'original_filename': file.filename,
            'encrypted_filename': encrypted_filename,
            'file_hash': file_hash,
            'uploaded_by': session['username'],
            'role': 'collector',
            'shared_with': ['localbody'],
            'created_at': datetime.now().isoformat(),
            'type': 'encrypted_file'
        })
        
        notifications_table.insert({
            'target_role': 'localbody',
            'message': f"New encrypted file uploaded by Collector: {file.filename}",
            'from_user': session['username'],
            'created_at': datetime.now().isoformat(),
            'read': False
        })
        
        flash('File encrypted and uploaded successfully', 'success')
    
    Document = Query()
    files = documents_table.search((Document.role == 'collector') & (Document.type == 'encrypted_file'))
    return render_template('collector/upload_file.html', files=files)

@app.route('/collector/view-orders')
@login_required
@role_required('collector')
def collector_view_orders():
    Order = Query()
    orders = orders_table.search(Order.target_roles.any(['collector']))
    return render_template('collector/view_orders.html', orders=orders)

@app.route('/collector/share-data', methods=['GET', 'POST'])
@login_required
@role_required('collector')
def collector_share_data():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        share_with = request.form.getlist('share_with')
        
        documents_table.insert({
            'title': title,
            'content': content,
            'shared_with': share_with,
            'uploaded_by': session['username'],
            'role': 'collector',
            'created_at': datetime.now().isoformat(),
            'type': 'shared_data'
        })
        
        flash('Data shared successfully', 'success')
    
    Document = Query()
    shared_docs = documents_table.search((Document.role == 'collector') & (Document.type == 'shared_data'))
    gov_docs = documents_table.search((Document.shared_with.any(['collector'])))
    return render_template('collector/share_data.html', my_documents=shared_docs, received_documents=gov_docs)

@app.route('/collector/download-encrypted/<int:doc_id>')
@login_required
@role_required('collector')
def collector_download_encrypted(doc_id):
    doc = documents_table.get(doc_id=doc_id)
    if doc and doc['type'] == 'encrypted_file':
        if doc['uploaded_by'] != session['username']:
            flash('You do not have permission to download this file', 'error')
            return redirect(url_for('collector_upload_file'))
        filepath = os.path.join(ENCRYPTED_FOLDER, doc['encrypted_filename'])
        return send_file(filepath, as_attachment=True, download_name=doc['encrypted_filename'])
    flash('File not found', 'error')
    return redirect(url_for('collector_upload_file'))

@app.route('/collector/notifications')
@login_required
@role_required('collector')
def collector_notifications():
    Notification = Query()
    notifications = notifications_table.search(Notification.target_role == 'collector')
    for n in notifications:
        if 'read' not in n:
            notifications_table.update({'read': False}, doc_ids=[n.doc_id])
            n['read'] = False
        n['id'] = n.doc_id
    return render_template('collector/notifications.html', notifications=notifications)
@app.route('/collector/notifications/mark-read/<int:notif_id>', methods=['POST'])
@login_required
@role_required('collector')
def collector_mark_notification_read(notif_id):
    notifications_table.update({'read': True}, doc_ids=[notif_id])
    return redirect(url_for('collector_notifications'))
@app.route('/collector/notifications/mark-all-read', methods=['POST'])
@login_required
@role_required('collector')
def collector_mark_all_notifications_read():
    Notification = Query()
    notifications_table.update({'read': True}, Notification.target_role == 'collector')
    return redirect(url_for('collector_notifications'))

@app.route('/collector/view-reports')
@login_required
@role_required('collector')
def collector_view_reports():
    Document = Query()
    reports = documents_table.search(Document.type == 'report')
    return render_template('collector/view_reports.html', reports=reports)

@app.route('/localbody/dashboard')
@login_required
@role_required('localbody')
def localbody_dashboard():
    Document = Query()
    Order = Query()
    Notification = Query()
    username = session.get('username')

    active_orders = orders_table.search(Order.target_roles.any(['localbody']))
    received_files = documents_table.search(
        (Document.type == 'encrypted_file') & (Document.shared_with.any(['localbody']))
    )
    submitted_reports = documents_table.search(
        (Document.uploaded_by == username) & (Document.type == 'report')
    )
    notifications = notifications_table.search(
        (Notification.target_role == 'localbody') & (Notification.read == False)
    )

    return render_template('localbody/dashboard.html',
        active_orders=len(active_orders),
        files_received=len(received_files),
        reports_submitted=len(submitted_reports),
        new_notifications=len(notifications)
    )

@app.route('/localbody/view-files')
@login_required
@role_required('localbody')
def localbody_view_files():
    Document = Query()
    files = documents_table.search((Document.type == 'encrypted_file') & (Document.shared_with.any(['localbody'])))
    return render_template('localbody/view_files.html', files=files)

@app.route('/localbody/download-encrypted/<int:doc_id>')
@login_required
@role_required('localbody')
def localbody_download_encrypted(doc_id):
    doc = documents_table.get(doc_id=doc_id)
    if doc and doc['type'] == 'encrypted_file':
        if 'localbody' not in doc.get('shared_with', []):
            flash('You do not have permission to download this file', 'error')
            return redirect(url_for('localbody_view_files'))
        filepath = os.path.join(ENCRYPTED_FOLDER, doc['encrypted_filename'])
        return send_file(filepath, as_attachment=True, download_name=doc['encrypted_filename'])
    flash('File not found', 'error')
    return redirect(url_for('localbody_view_files'))

@app.route('/localbody/download-decrypted/<int:doc_id>')
@login_required
@role_required('localbody')
def localbody_download_decrypted(doc_id):
    doc = documents_table.get(doc_id=doc_id)
    if doc and doc['type'] == 'encrypted_file':
        if 'localbody' not in doc.get('shared_with', []):
            flash('You do not have permission to download this file', 'error')
            return redirect(url_for('localbody_view_files'))
        
        encrypted_filepath = os.path.join(ENCRYPTED_FOLDER, doc['encrypted_filename'])
        
        with open(encrypted_filepath, 'r') as f:
            enc_data = json.load(f)
        
        decrypted_data = decrypt_file(enc_data['iv'], enc_data['data'])
        
        decrypted_filename = f"dec_{doc['original_filename']}"
        decrypted_path = os.path.join(DECRYPTED_FOLDER, decrypted_filename)
        
        with open(decrypted_path, 'wb') as f:
            f.write(decrypted_data)
        
        return send_file(decrypted_path, as_attachment=True, download_name=doc['original_filename'])
    
    flash('File not found', 'error')
    return redirect(url_for('localbody_view_files'))

@app.route('/localbody/view-orders')
@login_required
@role_required('localbody')
def localbody_view_orders():
    Order = Query()
    orders = orders_table.search(Order.target_roles.any(['localbody']))
    return render_template('localbody/view_orders.html', orders=orders)

@app.route('/localbody/share-data', methods=['GET', 'POST'])
@login_required
@role_required('localbody')
def localbody_share_data():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        share_with = request.form.getlist('share_with')
        
        documents_table.insert({
            'title': title,
            'content': content,
            'shared_with': share_with,
            'uploaded_by': session['username'],
            'role': 'localbody',
            'created_at': datetime.now().isoformat(),
            'type': 'shared_data'
        })
        
        flash('Data shared successfully', 'success')
    
    Document = Query()
    shared_docs = documents_table.search((Document.role == 'localbody') & (Document.type == 'shared_data'))
    received_docs = documents_table.search((Document.shared_with.any(['localbody'])))
    return render_template('localbody/share_data.html', my_documents=shared_docs, received_documents=received_docs)

@app.route('/localbody/upload-report', methods=['GET', 'POST'])
@login_required
@role_required('localbody')
def localbody_upload_report():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        report_type = request.form['report_type']
        
        documents_table.insert({
            'title': title,
            'content': content,
            'report_type': report_type,
            'uploaded_by': session['username'],
            'role': 'localbody',
            'shared_with': ['government', 'collector'],
            'created_at': datetime.now().isoformat(),
            'type': 'report'
        })
        
        notifications_table.insert({
            'target_role': 'government',
            'message': f"New report from Local Body: {title}",
            'from_user': session['username'],
            'created_at': datetime.now().isoformat(),
            'read': False
        })
        
        notifications_table.insert({
            'target_role': 'collector',
            'message': f"New report from Local Body: {title}",
            'from_user': session['username'],
            'created_at': datetime.now().isoformat(),
            'read': False
        })
        
        flash('Report submitted successfully', 'success')
    
    Document = Query()
    reports = documents_table.search((Document.role == 'localbody') & (Document.type == 'report'))
    return render_template('localbody/upload_report.html', reports=reports)

@app.route('/localbody/notifications')
@login_required
@role_required('localbody')
def localbody_notifications():
    Notification = Query()
    notifications = notifications_table.search(Notification.target_role == 'localbody')
    for n in notifications:
        if 'read' not in n:
            notifications_table.update({'read': False}, doc_ids=[n.doc_id])
            n['read'] = False
        n['id'] = n.doc_id
    return render_template('localbody/notifications.html', notifications=notifications)
    
@app.route('/localbody/notifications/mark-read/<int:notif_id>', methods=['POST'])
@login_required
@role_required('localbody')
def localbody_mark_notification_read(notif_id):
    notifications_table.update({'read': True}, doc_ids=[notif_id])
    return redirect(url_for('localbody_notifications'))
@app.route('/localbody/notifications/mark-all-read', methods=['POST'])
@login_required
@role_required('localbody')
def localbody_mark_all_notifications_read():
    Notification = Query()
    notifications_table.update({'read': True}, Notification.target_role == 'localbody')
    return redirect(url_for('localbody_notifications'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
