#Database initialization and helper functions
# import necessary modules
import sqlite3
import os
import shutil
from datetime import datetime
 
# Detect if running on Azure App Service
RUNNING_IN_AZURE = (
    "WEBSITE_SITE_NAME"
    in os.environ
)
 
if RUNNING_IN_AZURE:
    DB_PATH = "/home/invoices2.db"
else:
    DB_PATH = "invoices2.db"
 
 
# Ensure DB exists in /home (Azure writable directory)
# Ensure DB exists in the correct location
if not os.path.exists(DB_PATH):
    if RUNNING_IN_AZURE:
        # On Azure: copy DB from wwwroot if included in ZIP
        if os.path.exists("invoices2.db"):
            shutil.copy("invoices2.db", DB_PATH)
        else:
            # Create a new DB from schema
            connection = sqlite3.connect(DB_PATH)
            with open('schema.sql') as f:
                connection.executescript(f.read())
            connection.commit()
            connection.close()
    else:
        # Local development: create DB normally
        connection = sqlite3.connect(DB_PATH)
        with open('schema.sql') as f:
            connection.executescript(f.read())
        connection.commit()
        connection.close()
 
 
# Database helper functions
# Open a connection to the database
def open_connection() -> sqlite3.Connection:
    """
    Function for open_connection
    Parameters: path
    Returns: sqlite3.Connection object
    """
    try:
        conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        raise
 
 
# Safe execute function with error handling
def safe_execute(query, params):
    """
    Execute a query safely with error handling
    Parameters: query, params
    Returns: cursor object after execution
    """
    conn = open_connection()
    cursor = conn.cursor()
   
    try:
        cursor.execute(query, params)
        conn.commit()
        return cursor
    except Exception as e:
        print(f"Database Error: {e}")
        conn.rollback()
        raise
 
 
# Fetch all invoices for view invoices page
def get_all_invoices():
    """
    Fetch all invoices for view invoices page
    Parameters: None
    Returns: List of all invoices
    """
    conn = open_connection()
    cursor = conn.cursor()
 
    query = (
        "SELECT invoices.*, customers.customer_name, "
        "customers.customer_address FROM invoices JOIN customers "
        "ON invoices.customer_id = customers.customer_id"
    )
 
    try:
        cursor.execute(query)
        invoices = cursor.fetchall()
        return invoices
    except Exception as e:
        print(f"Error fetching invoices: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
 
 
# Add a new invoice to the database
 
def add_invoice(invoice_no: int, customer_name: str, customer_address: str,
                date: datetime, item_description: str, total: float):
 
    conn = open_connection()
    cursor = conn.cursor()
 
    try:
        # Find existing customer or insert a new one
        cursor.execute(
            'SELECT customer_id FROM customers WHERE customer_name = ? AND customer_address = ?',
            (customer_name, customer_address)
        )
        row = cursor.fetchone()
        if row:
            customer_id = row['customer_id']
        else:
            cursor.execute(
                'INSERT INTO customers (customer_name, customer_address) VALUES (?, ?)',
                (customer_name, customer_address)
            )
            customer_id = cursor.lastrowid
 
        # Insert invoice linked to customer
        cursor.execute(
            'INSERT INTO invoices (customer_id, invoice_no, date, '
            'item_description, total) VALUES (?, ?, ?, ?, ?)',
            (customer_id, invoice_no, date, item_description, total)
        )
 
        conn.commit()
 
    except Exception as e:
        conn.rollback()
        print("Database Error:", e)
        raise
 
    finally:
        cursor.close()
        conn.close()
 
 
# Delete an invoice from the database
def delete_invoice(invoice_id):
    """
    Delete an invoice from the database.
    Parameters: invoice_id
    Returns: None, used for deleting an invoice record
    """
    query = 'DELETE FROM invoices WHERE invoice_id = ?'
    safe_execute(query, (invoice_id,))
 
 

 
def update_invoice(invoice_id, invoice_no, customer_name, customer_address,
                   date, item_description, total):
 
    conn = open_connection()
    cursor = conn.cursor()
 
    try:
        # Find or create the customer for the provided name/address
        cursor.execute(
            'SELECT customer_id FROM customers WHERE customer_name = ? AND customer_address = ?',
            (customer_name, customer_address)
        )
        row = cursor.fetchone()
        if row:
            new_customer_id = row['customer_id']
        else:
            cursor.execute(
                'INSERT INTO customers (customer_name, customer_address) VALUES (?, ?)',
                (customer_name, customer_address)
            )
            new_customer_id = cursor.lastrowid

        # Update invoice to point to the (existing or newly-created) customer
        cursor.execute(
            "UPDATE invoices SET customer_id = ?, invoice_no = ?, date = ?, item_description = ?, total = ? WHERE invoice_id = ?",
            (new_customer_id, invoice_no, date, item_description, total, invoice_id)
        )
 
        conn.commit()
 
    except Exception as e:
        conn.rollback()
        print("Database Error:", e)
        raise
 
    finally:
        cursor.close()
        conn.close()
 
 
# Search invoices based on field and query
def search_invoices(search_field, search_query):
    """
    Search invoices based on field and query
    Parameters: search_field, search_query
    Returns: List of invoices matching the search criteria
    """
    # Validate search_field to prevent SQL injection
    valid_fields = [
        'invoice_no', 'customer_name', 'customer_address',
        'date', 'item_description', 'total'
    ]
   
    if not search_field or not search_query:
        # If no search criteria, return all invoices
        return get_all_invoices()
   
    if search_field not in valid_fields:
        raise ValueError(f"Invalid search field: {search_field}")
   
    conn = open_connection()
    cursor = conn.cursor()
 
    try:
        # SQL LIKE for partial matches - now safe with validated field
        query = (
            f'SELECT invoices.*, customers.customer_name, '
            f'customers.customer_address FROM invoices JOIN customers '
            f'ON invoices.customer_id = customers.customer_id '
            f'WHERE {search_field} LIKE ?'
        )
 
        # Prevent SQL injection by using parameterized queries
        cursor.execute(query, (f'%{search_query}%',))
        invoices = cursor.fetchall()
        return invoices
    except Exception as e:
        print(f"Error searching invoices: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
 
 
# Fetch all customers
def get_all_customers():
    """
    Fetch all customers from the database
    Parameters: None
    Returns: List of all customers
    """
    conn = open_connection()
    cursor = conn.cursor()
 
    query = "SELECT * FROM customers ORDER BY customer_name"
 
    try:
        cursor.execute(query)
        customers = cursor.fetchall()
        return customers
    except Exception as e:
        print(f"Error fetching customers: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
 