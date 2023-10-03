from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sales.db'

db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    sales = db.relationship('Sale', backref='product', lazy=True)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    price = IntegerField('Price', validators=[DataRequired()])
    submit = SubmitField('Add Product')

class SaleForm(FlaskForm):
    product_id = IntegerField('Product ID', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    submit = SubmitField('Record Sale')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/remove_product/<int:product_id>', methods=['POST'])
def remove_product(product_id):
    product = Product.query.get_or_404(product_id)

    # Remove the associated sales records
    sales = Sale.query.filter_by(product_id=product_id).all()
    for sale in sales:
        db.session.delete(sale)

    db.session.delete(product)
    db.session.commit()
    flash(f'Product "{product.name}" removed successfully!', 'success')
    return redirect(url_for('products'))


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

        # Check if the specified product_id exists
        product = Product.query.get(product_id)
        if product:
            sale = Sale(product_id=product_id, quantity=quantity)
            db.session.add(sale)
            db.session.commit()
            flash(f'Sale recorded successfully!', 'success')
        else:
            flash(f'Invalid product ID. Please enter a valid product ID.', 'error')

    products = Product.query.all()
    sales = Sale.query.all()
    return render_template('sales.html', form=form, products=products, sales=sales)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
