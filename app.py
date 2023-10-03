from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField, HiddenField
from wtforms.validators import DataRequired
from datetime import datetime
import pytz

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sales.db'

db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Product', backref='sales')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    price = IntegerField('Price', validators=[DataRequired()])
    submit = SubmitField('Add Product')

class SaleForm(FlaskForm):
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    submit = SubmitField('Record Sale')

    def __init__(self, *args, **kwargs):
        super(SaleForm, self).__init__(*args, **kwargs)
        self.product_id.choices = [(product.id, product.name) for product in Product.query.all()]

class SessionForm(FlaskForm):
    start_session = SubmitField('Start Session')
    quit_session = SubmitField('Quit Session')
    session_start = HiddenField('Session Start')
    session_end = HiddenField('Session End')
    session_status = StringField('Session Status')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/products', methods=['GET', 'POST'])
def products():
    form = ProductForm()

    if form.validate_on_submit():
        name = form.name.data
        price = form.price.data
        product = Product(name=name, price=price)
        db.session.add(product)
        db.session.commit()
        flash(f'Product "{name}" added successfully!', 'success')

    products = Product.query.all()
    return render_template('products.html', form=form, products=products)

@app.route('/sales', methods=['GET', 'POST'])
def sales():
    form = SaleForm()

    if form.validate_on_submit():
        product_id = form.product_id.data
        quantity = form.quantity.data
        sale = Sale(product_id=product_id, quantity=quantity)
        db.session.add(sale)
        db.session.commit()
        flash(f'Sale recorded successfully!', 'success')

    products = Product.query.all()
    sales = Sale.query.all()
    return render_template('sales.html', form=form, products=products, sales=sales)

@app.route('/session', methods=['GET', 'POST'])
def manage_session():
    form = SessionForm()

    session_status = session.get('session_status', 'Not Started')

    if form.start_session.data:
        session['session_start'] = datetime.now(pytz.utc)
        form.session_start.data = session['session_start'].isoformat()
        session['session_status'] = 'Running'
        form.session_status.data = 'Running'
        flash('Session started!', 'info')

    if form.quit_session.data:
        session_start = session.pop('session_start', None)
        if session_start:
            session_end = datetime.now(pytz.utc)
            form.session_end.data = session_end.isoformat()
            session_duration = session_end - session_start
            flash(f'Session ended. Session duration: {session_duration}', 'info')
            session['session_status'] = 'Ended'
            form.session_status.data = 'Ended'

    return render_template('session.html', form=form, session_status=session_status)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
