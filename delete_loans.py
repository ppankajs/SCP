from app import app, db  # Import the Flask app and db
from app import Loan  # Import the Loan model

# Delete all loans in the database
def delete_all_loans():
    # Use the application context to interact with the database
    with app.app_context():
        try:
            db.session.query(Loan).delete()  # Delete all loans
            db.session.commit()  # Commit the transaction
            print("✅ All loan records deleted successfully.")
        except Exception as e:
            db.session.rollback()  # Rollback in case of an error
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    delete_all_loans()
