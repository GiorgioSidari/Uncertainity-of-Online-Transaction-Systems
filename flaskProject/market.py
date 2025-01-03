from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
import stripe
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Stripe Configuration
stripe.api_key = 'sk_test_Y17KokhC3SRYCQTLYiU5ZCD2'
YOUR_DOMAIN = 'http://localhost:5000'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///market.db'
db = SQLAlchemy(app)

# Database Model
class Item(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(length=30), nullable=False, unique=True)
    price = db.Column(db.Integer(), nullable=False)
    barcode = db.Column(db.String(length=12), nullable=False, unique=True)
    description = db.Column(db.String(length=1024), nullable=False, unique=True)

    def __repr__(self):
        return f'Item {self.name}'

@app.before_request
def create_and_seed_db():
    if not hasattr(app, 'db_initialized'):
        db.create_all()
        if not Item.query.first():  # Check if database is empty
            sample_items = [
                Item(name="Laptop", price=999, barcode="123456789012", description="A powerful laptop."),
                Item(name="iPhone", price=799, barcode="987654321098", description="A sleek smartphone."),
            ]
            db.session.add_all(sample_items)
            db.session.commit()
        app.db_initialized = True

@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')

@app.route('/market')
def market_page():
    try:
        items = Item.query.all()
        logging.debug(f"Retrieved items: {items}")
        return render_template('market.html', items=items)
    except Exception as e:
        logging.error(f"Error loading market page: {e}")
        return "Error loading market page", 500

@app.route('/create-checkout-session/<int:item_id>', methods=['POST'])
def create_checkout_session(item_id):
    try:
        logging.debug(f"Attempting to create checkout session for item ID: {item_id}")
        item = Item.query.get_or_404(item_id)
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': item.name,
                        },
                        'unit_amount': item.price * 100,  # Convert to cents
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success',
            cancel_url=YOUR_DOMAIN + '/cancel',
        )
        logging.debug("Checkout session created successfully")
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        logging.error(f"Error creating checkout session: {e}")
        return "Error creating checkout session", 500

@app.route('/success')
def success_page():
    return render_template('success.html')

@app.route('/cancel')
def cancel_page():
    return render_template('cancel.html')

if __name__ == '__main__':
    app.run(debug=True)
