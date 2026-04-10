-- db/init.sql
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    region VARCHAR(50)
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100),
    category VARCHAR(50),
    price DECIMAL(10, 2)
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    product_id INT REFERENCES products(product_id),
    order_date DATE,
    quantity INT,
    returned BOOLEAN DEFAULT FALSE
);

-- Insert dummy data so the agent has something to retrieve
INSERT INTO customers (name, email, region) VALUES 
('Alice Smith', 'alice@test.com', 'North America'),
('Ravi Kumar', 'ravi@test.com', 'Asia'),
('Elena Rossi', 'elena@test.com', 'Europe');

INSERT INTO products (product_name, category, price) VALUES 
('Mechanical Keyboard', 'Electronics', 150.00),
('Coffee Beans', 'Groceries', 20.00),
('Ergonomic Chair', 'Furniture', 300.00);

INSERT INTO orders (customer_id, product_id, order_date, quantity, returned) VALUES 
(1, 1, '2023-10-01', 2, FALSE),
(2, 1, '2023-10-05', 1, TRUE),
(3, 3, '2023-10-10', 1, FALSE),
(1, 2, '2023-10-12', 5, FALSE);

-- SECURITY: Create a read-only user for the AI
CREATE ROLE ai_agent WITH LOGIN PASSWORD 'readonly_pass';
GRANT CONNECT ON DATABASE business_sandbox TO ai_agent;
GRANT USAGE ON SCHEMA public TO ai_agent;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ai_agent;

-- ==========================================
-- ENTERPRISE SECURITY: ROW-LEVEL SECURITY (RLS)
-- ==========================================

-- 1. Turn on RLS for the tables
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

-- 2. Define ADMIN Policies (Can see everything)
CREATE POLICY admin_all_customers ON customers FOR SELECT 
USING (current_setting('app.current_role', true) = 'admin');

CREATE POLICY admin_all_orders ON orders FOR SELECT 
USING (current_setting('app.current_role', true) = 'admin');

CREATE POLICY admin_all_products ON products FOR SELECT 
USING (current_setting('app.current_role', true) = 'admin');

-- 3. Define EMPLOYEE Policies (Restricted Access)
-- Employees can ONLY see customers in North America
CREATE POLICY employee_na_customers ON customers FOR SELECT 
USING (current_setting('app.current_role', true) = 'employee' AND region = 'North America');

-- Employees can ONLY see orders attached to North American customers
CREATE POLICY employee_na_orders ON orders FOR SELECT 
USING (
    current_setting('app.current_role', true) = 'employee' AND 
    customer_id IN (SELECT customer_id FROM customers WHERE region = 'North America')
);

-- Employees can see all products (no restriction on the catalog)
CREATE POLICY employee_all_products ON products FOR SELECT 
USING (current_setting('app.current_role', true) = 'employee');

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ai_agent;