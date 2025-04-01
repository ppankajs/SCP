from flask import Flask, request, jsonify, redirect, render_template, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import re
import requests 
from functools import wraps

app = Flask(__name__)
CORS(app)

# Database setup (SQLite in this case)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loans.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '54eb414e2339dca3f9a929d44d127113ee794db9cbd43730cbc8ebf7c590a708'  # Required for sessions

db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)

# Association Table (Intermediate Table)
user_loans = db.Table('user_loans',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('loan_id', db.String, db.ForeignKey('loan.loanId'), primary_key=True)
)

# Loan model (database table)
class Loan(db.Model):
    loanId = db.Column(db.String, primary_key=True, unique=True, nullable=False)
    bank = db.Column(db.String, nullable=False)
    interestRate = db.Column(db.Float, nullable=False)
    maxLoanAmount = db.Column(db.Float, nullable=False)
    tenure = db.Column(db.String, nullable=False)
    monthlyEMI = db.Column(db.Float, nullable=False)
    processingFee = db.Column(db.Float, nullable=False)
    prepaymentPenalty = db.Column(db.String, nullable=False)
    scheme = db.Column(db.String, nullable=False)

    users = db.relationship('User', secondary=user_loans, backref=db.backref('loans', lazy=True))

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

# Create tables in the database (if they don't already exist)
with app.app_context():
    db.create_all()

# Strict Name, Email, and Password Validation
# @app.route('/signup', methods=['GET', 'POST'])
# def signup():
#     if request.method == 'GET':
#         return render_template('signup.html')

#     data = request.form
#     name = data.get('name')
#     email = data.get('email')
#     password = data.get('password')
    
#     if not name or not email or not password:
#         flash("All fields are required", "danger")
#         return redirect(url_for('signup'))

#     # Strict Name Validation (Only Alphabets)
#     if not re.match(r'^[A-Za-z ]+$', name):  
#         flash('Name must contain only alphabets.', 'danger')
#         return redirect(url_for('signup'))

#     # Strict Email Validation
#     email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
#     if not re.match(email_regex, email):
#         flash('Invalid email address format. Please enter a valid email.', 'danger')
#         return redirect(url_for('signup'))

#     # Password Complexity Validation
#     password_regex = r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$'
#     if not re.match(password_regex, password):
#         flash('Password must contain at least one uppercase letter, one number, one special character, and be at least 6 characters long.', 'danger')
#         return redirect(url_for('signup'))

#     # Check if Email Already Exists
#     if User.query.filter_by(email=email).first():
#         flash('User already exists. Please log in.', 'warning')
#         return redirect(url_for('login'))

#     # Hash Password & Store User
#     hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
#     new_user = User(name=name, email=email, password=hashed_password)

#     db.session.add(new_user)
#     db.session.commit()

#     flash('Registration successful! Please login.', 'success')
#     return redirect(url_for('login'))  # Redirect after successful signup

EMAIL_API_URL = "http://GenericEmailSendingApi-env.eba-34zkmvsr.us-east-1.elasticbeanstalk.com/api/sendemail"
BEARER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEsImlhdCI6MTc0MTY1NDQyOX0.FKCNiMFGrS5SR45kBxp6fbglPx5CXmrHH56GjqXQeRY"

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')

    data = request.form
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not name or not email or not password:
        flash("All fields are required", "danger")
        return redirect(url_for('signup'))

    if not re.match(r'^[A-Za-z ]+$', name):  
        flash('Name must contain only alphabets.', 'danger')
        return redirect(url_for('signup'))

    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, email):
        flash('Invalid email address format.', 'danger')
        return redirect(url_for('signup'))

    password_regex = r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$'
    if not re.match(password_regex, password):
        flash('Password must meet complexity requirements.', 'danger')
        return redirect(url_for('signup'))

    if User.query.filter_by(email=email).first():
        flash('User already exists. Please log in.', 'warning')
        return redirect(url_for('login'))

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(name=name, email=email, password=hashed_password)

    db.session.add(new_user)
    db.session.commit()

    # 📧 **Send Email Notification**
    email_payload = {
        "to": email,
        "subject": "Welcome to Our Platform",
        "body": f"Hello {name},\n\nThank you for signing up! We're excited to have you on board.\n\nBest regards,\nYour Team"
    }

    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(EMAIL_API_URL, json=email_payload, headers=headers)
        if response.status_code == 200:
            flash("Registration successful! A confirmation email has been sent.", "success")
        else:
            flash("Registration successful, but email sending failed.", "warning")
    except Exception as e:
        flash(f"Registration successful, but email sending failed. Error: {str(e)}", "warning")

    return redirect(url_for('login'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        flash("Invalid credentials", "danger")
        return redirect(url_for('login'))

    # Store user info in session
    session['user_id'] = user.id
    session['user_name'] = user.name
    flash("Login successful!", "success")

    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user ID from session
    session.pop('user_name', None)  # Remove user name from session
    flash("Logged out successfully!", "info")
    return redirect(url_for('home'))


# Function to protect routes (login required)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("You need to be logged in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# @app.route('/')
# def home():
#     return render_template('home.html', user_name=session.get('user_name'))

@app.route('/')
def home():
    # Check if the user is logged in by looking at the session
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    # Fetch all loans from the database
    loans = Loan.query.all()

    return render_template('home.html', user_name=session.get('user_name'), loans=loans)


# Protected route (accessible only if logged in)
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=session.get('user_name'))


# Loan details endpoint
@app.route('/loan-details/add', methods=['POST'])
def add_loan_details():
    data = request.get_json()

    required_fields = ['loanId', 'bank', 'interestRate', 'maxLoanAmount', 'tenure', 'monthlyEMI', 'processingFee', 'prepaymentPenalty', 'scheme']
    if not data or not all(key in data for key in required_fields):
        return jsonify({"status": 400, "error": "Missing required fields"}), 400

    # Check if loanId already exists
    existing_loan = Loan.query.filter_by(loanId=data['loanId']).first()
    if existing_loan:
        return jsonify({"status": 409, "error": "Loan ID already exists"}), 409

    # Create a new loan record
    new_loan = Loan(
        loanId=data['loanId'],
        bank=data['bank'],
        interestRate=data['interestRate'],
        maxLoanAmount=data['maxLoanAmount'],
        tenure=data['tenure'],
        monthlyEMI=data['monthlyEMI'],
        processingFee=data['processingFee'],
        prepaymentPenalty=data['prepaymentPenalty'],
        scheme=data['scheme']
    )

    # Add the new loan to the database
    db.session.add(new_loan)
    db.session.commit()

    return jsonify({"status": 200, "message": "Loan added successfully", "loanId": new_loan.loanId}), 200


@app.route('/loan-details/', methods=['GET'])
def get_loans_by_scheme():
    scheme = request.args.get('scheme')

    if not scheme:
        return jsonify({"status": 400, "error": "Scheme parameter is required"}), 400

    loans = Loan.query.filter_by(scheme=scheme).all()

    if not loans:
        return jsonify({"status": 404, "error": "No loans found for the provided scheme"}), 404

    loan_data = []
    for loan in loans:
        loan_data.append({
            "loanId": loan.loanId,
            "bank": loan.bank,
            "interestRate": loan.interestRate,
            "maxLoanAmount": loan.maxLoanAmount,
            "tenure": loan.tenure,
            "monthlyEMI": loan.monthlyEMI,
            "processingFee": loan.processingFee,
            "prepaymentPenalty": loan.prepaymentPenalty,
            "scheme": loan.scheme
        })

    return jsonify({"status": 200, "loans": loan_data}), 200


if __name__ == '__main__':
    app.run(debug=True)
