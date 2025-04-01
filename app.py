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
    
class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', name='fk_purchase_user'),
        nullable=False
    )
    property_name = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    location = db.Column(db.String, nullable=False)
    property_type = db.Column(db.String, nullable=False)
    loan_id = db.Column(
        db.String,
        db.ForeignKey('loan.loanId', name='fk_purchase_loan'),
        nullable=True
    )
    loan = db.relationship('Loan')


# Create tables in the database (if they don't already exist)
with app.app_context():
    db.create_all()
    
    
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("You need to be logged in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/buy-property', methods=['POST'])
@login_required
def buy_property():
    user_id = session['user_id']
    property_name = request.form.get('property_name')
    price = float(request.form.get('price'))
    location = request.form.get('location')
    property_type = request.form.get('property_type')
    loan_id = request.form.get('loan_id')  # use selected loan_id from form

    new_purchase = Purchase(
        user_id=user_id,
        property_name=property_name,
        price=price,
        location=location,
        property_type=property_type,
        loan_id=loan_id
    )

    db.session.add(new_purchase)
    db.session.commit()
    flash("Property purchased successfully!", "success")
    return redirect(url_for('profile'))


# API URLs and Tokens
SUBSCRIPTION_EMAIL = "http://GenericEmailSendingApi-env.eba-34zkmvsr.us-east-1.elasticbeanstalk.com/api/subscribe"
SEND_EMAIL = "http://GenericEmailSendingApi-env.eba-34zkmvsr.us-east-1.elasticbeanstalk.com/api/sendemail"
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

    try:
        sub_resp = requests.post(
            SUBSCRIPTION_EMAIL,
            json={"email": email, "userId": new_user.id},
            headers={
                "Authorization": f"Bearer {BEARER_TOKEN}",
                "Content-Type": "application/json"
            }
        )
        if sub_resp.status_code == 200:
            flash("Subscribed to notifications.", "info")
        else:
            flash("Signup success, but subscription failed.", "warning")
    except Exception as e:
        flash(f"Signup success, but subscription error: {str(e)}", "warning")

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

    session['user_id'] = user.id
    session['user_name'] = user.name
    flash("Login successful!", "success")

    try:
        email_data = {
            "userId": user.id,
            "email": email,
            "subject": "Welcome Back to Buddy Loan",
            "message": f"Hello {user.name},\n\nYou have successfully logged in to Buddy Loan.\n\nIf this wasn't you, please reset your password.\n\nCheers,\nBuddy Loan Team"
        }
        email_resp = requests.post(
            SEND_EMAIL,
            json=email_data,
            headers={
                "Authorization": f"Bearer {BEARER_TOKEN}",
                "Content-Type": "application/json"
            }
        )
        
        print("🔁 Subscription Response Code:", email_resp.status_code)
        print("🔁 Subscription Response Body:", email_resp.text)
        
        if email_resp.status_code != 200:
            flash("Login email failed to send.", "warning")
    except Exception as e:
        flash(f"Logged in, but email error: {str(e)}", "warning")

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


PROPERTY_API_URL = "http://property-recommendation-env.eba-bc2bsfwz.us-east-1.elasticbeanstalk.com/recommend"

@app.route('/')
def home():
    # Check if the user is logged in by looking at the session
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    # Fetch all loans from the database
    loans = Loan.query.all()

    return render_template('home.html', user_name=session.get('user_name'), loans=loans)

@app.route('/properties')
@login_required
def show_all_properties():
    try:
        response = requests.get(PROPERTY_API_URL, timeout=10)
        if response.status_code != 200:
            flash("Failed to fetch properties", "danger")
            return redirect(url_for('home'))

        properties = response.json()
        loans = Loan.query.all()  # Make sure this is included

        return render_template('select_property.html', properties=properties, loans=loans)
    
    except requests.exceptions.RequestException as e:
        flash(f"Error fetching properties: {str(e)}", "danger")
        return redirect(url_for('home'))



@app.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    purchases = Purchase.query.filter_by(user_id=user.id).all()
    return render_template('profile.html', user=user, purchases=purchases)

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

def recommend_scheme(property_price):
    suitable_loans = Loan.query.filter(Loan.maxLoanAmount >= property_price).order_by(Loan.interestRate.asc()).all()
    if suitable_loans:
        return suitable_loans[0]  # Return best suited loan
    return None

@app.route('/delete-purchase/<int:purchase_id>', methods=['POST'])
@login_required
def delete_purchase(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)

    # Ensure the logged-in user owns this purchase
    if purchase.user_id != session['user_id']:
        flash("You are not authorized to delete this purchase.", "danger")
        return redirect(url_for('profile'))

    db.session.delete(purchase)
    db.session.commit()
    flash("Property purchase deleted successfully.", "success")
    return redirect(url_for('profile'))

@app.route('/all-loans', methods=['GET'])
def all_loans():
    # Fetch all loans grouped by scheme
    loans = Loan.query.all()

    # Organize them into a dictionary: { scheme_name: [loan1, loan2, ...] }
    grouped_loans = {}
    for loan in loans:
        grouped_loans.setdefault(loan.scheme, []).append(loan)

    return render_template('all_loans.html', grouped_loans=grouped_loans)


if __name__ == '__main__':
    app.run(debug=True)
