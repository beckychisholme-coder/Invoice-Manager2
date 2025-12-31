-- Schema for Customers and Invoices Tables
 
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS customers;
 
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT NOT NULL,
    customer_address TEXT NOT NULL
);

-- Ensure customers with the same name+address are unique
CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_unique ON customers(customer_name, customer_address);
 
CREATE TABLE invoices (
    invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    invoice_no INTEGER NOT NULL,
    item_description TEXT NOT NULL,
    total REAL NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
 
 