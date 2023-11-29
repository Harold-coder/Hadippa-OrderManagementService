# Continue from your existing imports
from flask import Flask, render_template, request, redirect, url_for
import psycopg2
from datetime import datetime

app = Flask(__name__)

# ... (existing functions and routes)

def get_db_connection():
    # Use your existing database connection details
    connection = psycopg2.connect(
        host='db-cc.co4twflu4ebv.us-east-1.rds.amazonaws.com',
        port=5432,
        user='master',
        password='MasterPassword',
        database='lion_leftovers'
    )
    return connection

@app.route('/student_order', methods=['GET', 'POST'])
def student_order():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        student_uni = request.form['student_uni']
        inventory_id = request.form['inventory_id']
        quantity = request.form['quantity']

        # Calculate total price
        cursor.execute("SELECT Price FROM Inventory WHERE InventoryID = %s", (inventory_id,))
        price_per_item = cursor.fetchone()[0]
        total_price = price_per_item * int(quantity)

        # Fetch the current maximum OrderID
        cursor.execute("SELECT MAX(OrderID) FROM Orders")
        max_order_id = cursor.fetchone()[0]
        new_order_id = max_order_id + 1 if max_order_id else 1

        cursor.execute(
            "INSERT INTO Orders (OrderID, StudentUNI, InventoryID, OrderQuantity, TotalPrice) VALUES (%s, %s, %s, %s, %s)",
            (new_order_id, student_uni, inventory_id, quantity, total_price))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('student_order'))

    cursor.execute("SELECT InventoryID, FoodItem FROM Inventory")
    food_items = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('student_order.html', food_items=food_items)
@app.route('/manage_orders', methods=['GET', 'POST'])
def manage_orders():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if there's a search query
    search_uni = request.args.get('search_uni')

    if request.method == 'POST':
        action = request.form.get('action')
        order_id = request.form.get('order_id')

        if action == 'update':
            new_quantity = request.form['new_quantity']
            cursor.execute("UPDATE Orders SET OrderQuantity = %s WHERE OrderID = %s", (new_quantity, order_id))
        elif action == 'delete':
            cursor.execute("DELETE FROM Orders WHERE OrderID = %s", (order_id,))
        conn.commit()

    # Modify the SQL query to filter by UNI if there's a search query
    if search_uni:
        cursor.execute("SELECT * FROM Orders WHERE StudentUNI = %s", (search_uni,))
    else:
        cursor.execute("SELECT * FROM Orders")

    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('manage_orders.html', orders=orders)

@app.route("/")
def index():
    return render_template('index.html')


# ... (other routes and functions)

if __name__ == '__main__':
    app.run(debug=True)
