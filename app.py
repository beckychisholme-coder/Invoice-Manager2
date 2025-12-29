# app.py
# Main application file for the Invoice Management System
 
# Imports
from flask import Flask, render_template, request, redirect, url_for
from init_db import *
app = Flask(__name__)
 
 
 
# Main page route
@app.route('/')
def index():
    """
    Function for index
    Parameters: None
    Returns: Renders the home page with the index.html template
    """
    return render_template('index.html')
 
# New Invoice route
@app.route('/New Invoice', methods=['GET', 'POST'])
def new_invoice()-> str:
    """
    Function for new_invoice
    Parameters: None
    Returns: Renders the NewInvoice.html template or redirects to view invoices page after adding new invoice
    """
    if request.method == 'POST':
        # Error handling for form validation
        errors = validate_invoice_form(request.form)
        if errors:
            return render_template('NewInvoice.html', error_message=errors)
       
        try:
            add_invoice(
                request.form['invoice_no'],
                request.form['customer_name'],
                request.form['customer_address'],
                request.form['date'],
                request.form['item_description'],
                request.form['total']
            )
            # After adding, redirect to view invoices page
            return redirect(url_for('view_invoices'))
        except Exception as e:
            return render_template('NewInvoice.html', error_message=f"Database error: {str(e)}")
 
    return render_template('NewInvoice.html', title='Create a New Invoice')
 
 
# View Invoices route
@app.route('/View Invoices')
def view_invoices() -> str:
    """
    Function for view_invoices
    Parameters: None
    Returns: Renders the ViewInvoices.html template with invoice data
    """
 
    # Get search parameters
    search_query = request.args.get('search_query', '')
    search_field = request.args.get('search_field', '')
 
    try:
        # Fetch invoices based on search criteria
        if search_query and search_field:
            invoices = search_invoices(search_field, search_query)
        else:
            invoices = get_all_invoices()
       
        return render_template('ViewInvoices.html', invoices=invoices, search_query=search_query, search_field=search_field)
    except Exception as e:
        return render_template('error.html', message=f"Error fetching invoices: {str(e)}"), 500
 
 
# View Customers route
@app.route('/View Customers')
def view_customers() -> str:
    """
    Function for view_customers
    Parameters: None
    Returns: Renders the ViewCustomers.html template with customer data
    """
    try:
        customers = get_all_customers()
        return render_template('ViewCustomers.html', customers=customers)
    except Exception as e:
        return render_template('error.html', message=f"Error fetching customers: {str(e)}"), 500
 
 
# Delete Invoice route
@app.route('/delete/<int:invoice_id>')
def delete_invoice_route(invoice_id: int):
    """
    Function for delete_invoice_route
    Parameters: invoice_id
    Returns: redirects to view invoices page after deletion
    """
    try:
        delete_invoice(invoice_id)
        return redirect(url_for('view_invoices'))
    except Exception as e:
        return render_template('error.html', message=f"Error deleting invoice: {str(e)}"), 500
 
# Update Invoice route
@app.route('/update/<int:invoice_id>', methods=['GET', 'POST'])
def update_invoice_route(invoice_id : int):
    """
    Function for update_invoice_route
   
    Parameters: invoice_id
    Returns: updates form to invoice details and redirects to view invoices page after update
    """
    if request.method == 'POST':
        # Error handling for form validation
        errors = validate_invoice_form(request.form)
 
        if errors:
            try:
                conn = open_connection()
                cursor = conn.cursor()
                invoice = cursor.execute(
                    'SELECT invoices.*, customers.customer_name, '
                    'customers.customer_address FROM invoices JOIN customers '
                    'ON invoices.customer_id = customers.customer_id '
                    'WHERE invoices.invoice_id = ?',
                    (invoice_id,)
                ).fetchone()
                cursor.close()
                conn.close()
                return render_template('UpdateInvoice.html', invoice=invoice, error_message=errors)
            except Exception as e:
                return render_template('error.html', message=f"Error fetching invoice: {str(e)}"), 500
       
        invoice_no = request.form['invoice_no']
        customer_name = request.form['customer_name']
        customer_address = request.form['customer_address']
        date = request.form['date']
        item_description = request.form['item_description']
        total = request.form['total']
 
        try:
            update_invoice(invoice_id, invoice_no, customer_name, customer_address, date, item_description, total)
            return redirect(url_for('view_invoices'))
        except Exception as e:
            return render_template('error.html', message=f"Error updating invoice: {str(e)}"), 500
   
    # Error handling for fetching invoice details
    try:
        conn = open_connection()
        cursor = conn.cursor()
        invoice = cursor.execute(
            'SELECT invoices.*, customers.customer_name, '
            'customers.customer_address FROM invoices JOIN customers '
            'ON invoices.customer_id = customers.customer_id '
            'WHERE invoices.invoice_id= ?',
            (invoice_id,)
        ).fetchone()
        cursor.close()
        conn.close()
       
        if invoice is None:
            return render_template('error.html', message="Invoice not found"), 404
       
    except Exception as e:
        return render_template('error.html', message=f"Error fetching invoice: {str(e)}"), 500
 
    # Logic to fetch invoice details and render update form
    return render_template('UpdateInvoice.html', invoice=invoice)
 
 
#  General Error Handlers
@app.errorhandler(404)
def not_found(e):
    """
    Function for not_found
    Parameters: e: Description
    Returns: Description
    """
    return render_template('error.html', message="Page not found."), 404
 
 
@app.errorhandler(500)
def server_error(e):
    """
    Function for server_error
    Parameters: e: Description
    Returns: Description
    """
    return render_template('error.html', message="Internal server error."), 500
 
 
# Form validation function
# Checks data types and required fields
def validate_invoice_form(form: dict) -> list:
    """
    Validate invoice form data
   
    Parameters: form: Description
    Returns: List of error messages
    """
    errors = []
 
    # Invoice number
    try:
        invoice_no = int(form.get('invoice_no', '').strip())
        if invoice_no <= 0:
            errors.append("Invoice number must be a positive integer.")
    except ValueError:
        errors.append("Invoice number must be a valid integer.")
 
    # Customer name
    customer_name = form.get('customer_name', '').strip()
    if not customer_name:
        errors.append("Customer name is required.")
 
    # Address
    customer_address = form.get('customer_address', '').strip()
    if not customer_address:
        errors.append("Customer address is required.")
 
    # Date
    date = form.get('date', '').strip()
    if not date:
        errors.append("Date is required.")
 
    # Description
    item_description = form.get('item_description', '').strip()
    if not item_description:
        errors.append("Item description is required.")
 
    # Total
    try:
        total = float(form.get('total', '').strip())
        if total < 0:
            errors.append("Total cannot be negative.")
    except ValueError:
        errors.append("Total must be a valid number.")
 
    return errors
 
 
if __name__ == '__main__':
    app.run(debug=True)
 
 
 