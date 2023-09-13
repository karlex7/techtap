from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
import random
import string
import qrcode
from io import BytesIO

app = Flask(__name__)

# Configuration for Flask, SQLAlchemy, and Flask-Login
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Kj8x23kk@localhost:5432/techtap'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:Kj8x23kk@techta-y90i.cqukbkkjztbh.eu-west-1.rds.amazonaws.com:5432/techtap'
app.config['SECRET_KEY'] = 'your_secret_key_here'

db = SQLAlchemy(app)

# Flask-Login Configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'  # specify the route for logging in

# Dummy admin data for the sake of this example
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password123'  # In a real-world scenario, you'd store a hashed password

class AdminUser(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USERNAME:
        return AdminUser(user_id)
    return None

class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(500), nullable=False)
    short_url = db.Column(db.String(100), nullable=False, unique=True)

def generate_short_url():
    characters = string.ascii_letters + string.digits
    short_url = ''.join(random.choice(characters) for i in range(6))
    link = URL.query.filter_by(short_url=short_url).first()
    while link:
        short_url = ''.join(random.choice(characters) for i in range(6))
        link = URL.query.filter_by(short_url=short_url).first()
    return short_url

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_url():
    original_url = request.form['url']
    short_url = generate_short_url()
    new_url = URL(original_url=original_url, short_url=short_url)
    db.session.add(new_url)
    db.session.commit()
    flash(f'Your short URL is: {request.host_url}{short_url}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/<short_url>')
def redirect_to_original(short_url):
    url = URL.query.filter_by(short_url=short_url).first_or_404()
    return redirect(url.original_url)

@app.route('/list')
def list_urls():
    urls = URL.query.all()
    return render_template('list.html', urls=urls)

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_url(id):
    url = URL.query.get_or_404(id)
    if request.method == 'POST':
        url.original_url = request.form['url']
        db.session.commit()
        flash('URL Updated Successfully!', 'success')
        return redirect(url_for('list_urls'))
    return render_template('update.html', url=url)

@app.route('/delete/<int:id>')
def delete_url(id):
    url = URL.query.get_or_404(id)
    db.session.delete(url)
    db.session.commit()
    flash('URL Deleted Successfully!', 'success')
    return redirect(url_for('list_urls'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            login_user(AdminUser(username))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('admin_login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/generate_qr/<short_url>')
def generate_qr(short_url):
    img = qrcode.make(request.host_url + short_url)
    # Convert QR code to bytes
    stream = BytesIO()
    img.save(stream, "PNG")
    stream.seek(0)
    return send_file(stream, mimetype="image/png")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
