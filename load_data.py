import boto3
import json
import mysql.connector
import pyodbc


# Load the data from the JSON file
with open('./data/data.json', 'r') as file:
    data = json.load(file)

def get_secret(secret_name):
    # Initialize a session using Amazon Secrets Manager
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager')

    # Get the secret value
    get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)

# Fetch the secret values
secret_name = "mssql_secrets"
secret_values = get_secret(secret_name)

cursor = None
conn = None

host=secret_values['host']
user=secret_values['username']
password=secret_values['password']
port=secret_values['port']

try:
    connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host};UID={user};PWD={password}'
    # Connect to the MySQL server (without specifying a database)
    conn = pyodbc.connect(connection_string, autocommit=True)
    
    cursor = conn.cursor()

    # Create the `sales` database
    cursor.execute("""
                   IF NOT EXISTS(SELECT * FROM sys.databases WHERE name = 'sales') 
                   BEGIN 
                   CREATE DATABASE [sales] 
                   END
                   """)
    cursor.execute("USE sales")
    print("Database 'sales' created successfully!")

    # Create the `products` table
    cursor.execute("""
                   IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='products' and xtype='U')
                    BEGIN   
                    CREATE TABLE products (
                        ProductID INT PRIMARY KEY,
                        ProductName VARCHAR(255) NOT NULL,
                        Description VARCHAR(MAX),
                        Price DECIMAL(10, 2) NOT NULL,
                        StockQuantity INT NOT NULL,
                        CategoryID INT
                    )
                   END
    """)
    print("Table 'products' created successfully!")

    # Create the `customers` table
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='customers' and xtype='U')
        BEGIN 
        CREATE TABLE customers (
            CustomerID INT PRIMARY KEY,
            FirstName VARCHAR(255) NOT NULL,
            LastName VARCHAR(255) NOT NULL,
            Email VARCHAR(255) UNIQUE NOT NULL,
            Address VARCHAR(MAX),
            Phone VARCHAR(15)
        )
        END
    """)
    print("Table 'customers' created successfully!")

    # Create the `orders` table
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='orders' and xtype='U')
        BEGIN 
        CREATE TABLE orders (
            OrderID INT PRIMARY KEY,
            CustomerID INT,
            ProductID INT,
            Quantity INT NOT NULL,
            OrderDate DATE NOT NULL,
            TotalPrice DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (CustomerID) REFERENCES customers(CustomerID),
            FOREIGN KEY (ProductID) REFERENCES products(ProductID)
        )
        END
    """)
    print("Table 'orders' created successfully!")

    # Insert data into the `products` table
    for product in data['Products']:
        cursor.execute("""
            INSERT INTO products (ProductID, ProductName, Description, Price, StockQuantity, CategoryID)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (product['ProductID'], product['ProductName'], product['Description'], product['Price'], product['StockQuantity'], product['CategoryID']))
    print("Data inserted into 'products' table successfully!")

    # Insert data into the `customers` table
    for customer in data['Customers']:
        cursor.execute("""
            INSERT INTO customers (CustomerID, FirstName, LastName, Email, Address, Phone)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (customer['CustomerID'], customer['FirstName'], customer['LastName'], customer['Email'], customer['Address'], customer['Phone']))
    print("Data inserted into 'customers' table successfully!")

    # Insert data into the `orders` table
    for order in data['Orders']:
        cursor.execute("""
            INSERT INTO orders (OrderID, CustomerID, ProductID, Quantity, OrderDate, TotalPrice)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (order['OrderID'], order['CustomerID'], order['ProductID'], order['Quantity'], order['OrderDate'], order['TotalPrice']))
    print("Data inserted into 'orders' table successfully!")

    cursor.execute("""
        IF OBJECT_ID('dbo.[vw_sales]', 'V') IS NOT NULL
            DROP VIEW dbo.[vw_sales]
        """)
    cursor.execute("""
                    CREATE VIEW [vw_sales] as
                    select o.orderid, o.customerid, o.productid, o.quantity, o.OrderDate, o.TotalPrice, p.ProductName, p.Price ProductPricePerUnit,
                    p.StockQuantity , c.FirstName + c.LastName CustomerName, c.Phone, c.Email, c.Address 
                    from orders o
                    join products p on o.ProductID = p.ProductID
                    join customers c on c.CustomerID = o.CustomerID
    """)
    print("'VW_SALES' view has been created successfully!")
    # Commit the transactions
    conn.commit()

except pyodbc.Error as err:
    print(f"Error: {err}")
finally:
    # Close the connection
    if cursor:
        cursor.close()
    if conn:
        conn.close()