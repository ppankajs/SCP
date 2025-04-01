from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from app import db, User  # Import necessary modules from your app (replace 'your_app_file' with your actual file name)

# Initialize Flask app and DB (you might already have this in your main app, just ensure the configuration is set)
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loans.db'  # Your database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '54eb414e2339dca3f9a929d44d127113ee794db9cbd43730cbc8ebf7c590a708'

db.init_app(app)
bcrypt = Bcrypt(app)

def delete_user_by_email(email):
    # Create an app context
    with app.app_context():
        # Find the user by email
        user = User.query.filter_by(email=email).first()

        if user:
            # Delete user
            db.session.delete(user)
            db.session.commit()
            print(f"User with email '{email}' has been successfully deleted.")
        else:
            print(f"No user found with the email '{email}'.")

if __name__ == '__main__':
    email_to_delete = input("Enter the email of the user you want to delete: ")
    delete_user_by_email(email_to_delete)
