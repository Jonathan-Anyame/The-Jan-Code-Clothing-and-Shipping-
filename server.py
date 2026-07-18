from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import sqlite3

from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-change-me')

DB_PATH = 'store.db'

@app.context_processor
def inject_user():
    """Make current_user available in all templates (username string or None)."""
    return {'current_user': session.get('user')}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT,
        description TEXT,
        price REAL,
        category TEXT,
        stock INTEGER,
        image TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        total REAL,
        status TEXT,
        tracking TEXT,
        created_at TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        product_id INTEGER,
        quantity INTEGER
    )''')
    
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("index.html", current_user=session.get('user'))

@app.route("/shop")
def shop():
    # Retail shop not active — focus is product finding & shipping.
    return redirect(url_for('buy_from_china'))

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    return redirect(url_for('buy_from_china'))

@app.route("/cart")
def view_cart():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""SELECT c.*, p.name, p.price FROM cart c 
                 JOIN products p ON c.product_id = p.id 
                 WHERE c.user_id = ?""", (session['user_id'],))
    cart_items = c.fetchall()
    conn.close()
    
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template("cart.html", cart_items=cart_items, total=total, current_user=session.get('user'))

@app.route("/api/cart/add", methods=['POST'])
def add_to_cart():
    if not session.get('user_id'):
        return jsonify({'success': False, 'message': 'Login required'}), 401
    
    data = request.get_json()
    product_id = data['product_id']
    quantity = data.get('quantity', 1)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT * FROM cart WHERE user_id = ? AND product_id = ?", (session['user_id'], product_id))
    existing = c.fetchone()
    
    if existing:
        c.execute("UPDATE cart SET quantity = quantity + ? WHERE user_id = ? AND product_id = ?", 
                 (quantity, session['user_id'], product_id))
    else:
        c.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?,?,?)",
                 (session['user_id'], product_id, quantity))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Added to cart'})

@app.route("/api/cart/remove/<int:item_id>", methods=['DELETE'])
def remove_from_cart(item_id):
    if not session.get('user_id'):
        return jsonify({'success': False}), 401
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM cart WHERE id = ? AND user_id = ?", (item_id, session['user_id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route("/checkout")
def checkout():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""SELECT c.*, p.name, p.price FROM cart c 
                 JOIN products p ON c.product_id = p.id 
                 WHERE c.user_id = ?""", (session['user_id'],))
    cart_items = c.fetchall()
    conn.close()
    
    if not cart_items:
        return redirect(url_for('view_cart'))
    
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template("checkout.html", cart_items=cart_items, total=total, current_user=session.get('user'))

@app.route("/api/order/create", methods=['POST'])
def create_order():
    if not session.get('user_id'):
        return jsonify({'success': False}), 401
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("""SELECT c.*, p.price FROM cart c 
                 JOIN products p ON c.product_id = p.id 
                 WHERE c.user_id = ?""", (session['user_id'],))
    cart_items = c.fetchall()
    
    if not cart_items:
        conn.close()
        return jsonify({'success': False, 'message': 'Cart empty'}), 400
    
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    tracking = f"TJC{session['user_id']}{int(datetime.now().timestamp())}"
    
    c.execute("INSERT INTO orders (user_id, total, status, tracking, created_at) VALUES (?,?,?,?,?)",
             (session['user_id'], total, 'pending', tracking, datetime.now().isoformat()))
    
    c.execute("DELETE FROM cart WHERE user_id = ?", (session['user_id'],))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'tracking': tracking})

@app.route("/orders")
def my_orders():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (session['user_id'],))
    orders = c.fetchall()
    conn.close()
    
    return render_template("orders.html", orders=orders, current_user=session.get('user'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        try:
            c.execute("INSERT INTO users (username, email, password) VALUES (?,?,?)",
                     (username, email, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except:
            conn.close()
            return render_template('register.html', error='Username or email already exists')
    
    return render_template('register.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['user'] = user['username']
            return redirect(url_for('home'))
        
        return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route("/buy-from-china")
def buy_from_china():
    return render_template('buy_from_china.html', current_user=session.get('user'))

@app.route("/shipping")
def shipping():
    return render_template('shipping.html', current_user=session.get('user'))

@app.route("/contact")
def contact():
    return render_template('contact.html', current_user=session.get('user'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
