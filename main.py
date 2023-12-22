from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from decimal import Decimal
import jwt

app = Flask(__name__)
SECRET_KEY = "hadippa"


# Function to establish a database connection
def get_db_connection():
    connection = psycopg2.connect(
        host='db-cc.co4twflu4ebv.us-east-1.rds.amazonaws.com',
        port=5432,
        user='master',
        password='MasterPassword',
        database='lion_leftovers'
    )
    return connection

# Helper function to convert Decimal types to strings for JSON serialization
def convert_decimal_to_float(data):
    for row in data:
        for key, value in row.items():
            if isinstance(value, Decimal):
                row[key] = float(value)
    return data

@app.route('/get_orders', methods=['GET'])
def get_orders():
    # Retrieve query parameters for uni and order_id (if they exist)
    uni = request.args.get('uni')
    order_id = request.args.get('order_id')

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Construct the base query
    query = "SELECT * FROM Orders"
    query_conditions = []
    query_params = []
    
    # Add conditions to the query based on the provided parameters
    if uni:
        query_conditions.append("StudentUNI = %s")
        query_params.append(uni)
    if order_id:
        query_conditions.append("OrderID = %s")
        query_params.append(order_id)
    
    # Combine conditions into the query if they exist
    if query_conditions:
        query += " WHERE " + " AND ".join(query_conditions)
    
    # Execute the query
    cursor.execute(query, query_params)
    orders = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Convert Decimal to float for JSON serialization
    orders = convert_decimal_to_float(orders)
    
    # Return the orders as a JSON response
    return jsonify(orders)

# Endpoint for placing a new order
@app.route('/place_order', methods=['POST'])
def place_order():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get data from JSON request body
    data = request.get_json()
    student_uni = data.get('student_uni')
    inventory_id = data.get('inventory_id')
    quantity = data.get('quantity', 0)

    # Fetch price per item from Inventory and calculate total price
    cursor.execute("SELECT Price FROM Inventory WHERE InventoryID = %s", (inventory_id,))
    price_per_item = cursor.fetchone()[0]
    total_price = price_per_item * int(quantity)

    # Fetch the next OrderID by finding the current maximum OrderID
    cursor.execute("SELECT MAX(OrderID) FROM Orders")
    max_order_id = cursor.fetchone()[0]
    new_order_id = max_order_id + 1 if max_order_id else 1

    # Insert the new order into the Orders table
    cursor.execute(
        "INSERT INTO Orders (OrderID, StudentUNI, InventoryID, OrderQuantity, TotalPrice) VALUES (%s, %s, %s, %s, %s)",
        (new_order_id, student_uni, inventory_id, quantity, total_price))
    conn.commit()

    cursor.close()
    conn.close()
    return jsonify({"success": "Order placed successfully"})

# Endpoint for deleting an order
@app.route('/delete_order', methods=['POST'])
def delete_order():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get data from JSON request body
    data = request.get_json()
    order_id = data.get('order_id')

    # Check if the order ID is provided
    if not order_id:
        cursor.close()
        conn.close()
        return jsonify({"error": "Order ID is required"}), 400

    # Execute the query to delete the order
    cursor.execute("DELETE FROM Orders WHERE OrderID = %s", (order_id,))
    deleted_rows = cursor.rowcount  # Get the number of rows affected

    # If no rows are affected, the order does not exist
    if deleted_rows == 0:
        conn.close()
        return jsonify({"error": "Order not found"}), 404

    # Commit the transaction and close the connection
    conn.commit()
    cursor.close()
    conn.close()

    # Return a success message
    return jsonify({"success": "Order deleted successfully"})


@app.route('/update_order', methods=['POST'])
def update_order():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Get data from JSON request body
    data = request.get_json()
    order_id = data.get('order_id')
    new_quantity = data.get('new_quantity')

    # Validate that the required fields are provided
    if not order_id or not new_quantity:
        cursor.close()
        conn.close()
        return jsonify({"error": "Order ID and new quantity must be provided"}), 400

    # Update order quantity
    cursor.execute("UPDATE Orders SET OrderQuantity = %s WHERE OrderID = %s", (new_quantity, order_id))
    updated_rows = cursor.rowcount  # Get the number of rows affected

    # If no rows are affected, the order does not exist
    if updated_rows == 0:
        conn.close()
        return jsonify({"error": "Order not found"}), 404

    # Commit changes and close connection
    conn.commit()
    cursor.close()
    conn.close()

    # Return a success response
    return jsonify({"success": "Order updated successfully"})


@app.route("/")
def index():
    return jsonify({"message": "Welcome to the Order Management API Hosted on Google Cloud!"})

@app.route('/token', methods=['GET'])
def get_token():
    try:
        token = jwt.encode({'user': 'test_user', 'exp': datetime.utcnow() + timedelta(minutes=30)}, SECRET_KEY, algorithm="HS256")
        return jsonify({'token': token})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/protected', methods=['GET'])
def protected():
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]  # Remove 'Bearer ' prefix
    else:
        return jsonify({'message': 'Token is missing or invalid!'}), 403

    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return jsonify({'message': 'Protected content', 'user': data['user']})
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired!'}), 403
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token!'}), 403


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8012)
