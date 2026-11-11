INSERT INTO products (name, description, category, price, stock, image_url)
SELECT v.name, v.description, v.category, v.price, v.stock, v.image_url
FROM (VALUES
('Wireless Headphones', 'Bluetooth headphones with noise cancellation and deep bass', 'Electronics', 2499.00, 20, 'https://placehold.co/600x600?text=Headphones'),
('Smartphone', 'Android smartphone with AMOLED display and high resolution camera', 'Electronics', 15999.00, 15, 'https://placehold.co/600x600?text=Smartphone'),
('Mechanical Keyboard', 'RGB mechanical gaming keyboard with tactile switches', 'Electronics', 3499.00, 25, 'https://placehold.co/600x600?text=Keyboard'),
('Wireless Mouse', 'Ergonomic wireless mouse with adjustable DPI', 'Electronics', 899.00, 30, 'https://placehold.co/600x600?text=Mouse'),
('Smart Watch', 'Fitness smartwatch with heart rate and activity tracking', 'Electronics', 2999.00, 18, 'https://placehold.co/600x600?text=Smartwatch'),

('Cotton T-Shirt', 'Comfortable casual cotton t-shirt for everyday wear', 'Fashion', 599.00, 40, 'https://placehold.co/600x600?text=Tshirt'),
('Running Shoes', 'Lightweight running shoes with cushioned sole', 'Fashion', 2199.00, 20, 'https://placehold.co/600x600?text=Shoes'),
('Denim Jeans', 'Regular fit blue denim jeans for men and women', 'Fashion', 1499.00, 25, 'https://placehold.co/600x600?text=Jeans'),
('Leather Backpack', 'Durable everyday backpack with multiple compartments', 'Fashion', 1899.00, 15, 'https://placehold.co/600x600?text=Backpack'),

('Electric Kettle', 'Stainless steel electric kettle with automatic shut off', 'Home & Kitchen', 1199.00, 20, 'https://placehold.co/600x600?text=Kettle'),
('Mixer Grinder', 'Powerful mixer grinder for blending and food preparation', 'Home & Kitchen', 3299.00, 12, 'https://placehold.co/600x600?text=Mixer'),
('Non Stick Cookware Set', 'Non stick cooking pan and cookware set for home kitchens', 'Home & Kitchen', 2499.00, 16, 'https://placehold.co/600x600?text=Cookware'),
('Table Lamp', 'LED study table lamp with adjustable brightness', 'Home & Kitchen', 799.00, 30, 'https://placehold.co/600x600?text=Lamp'),

('Yoga Mat', 'Non slip exercise yoga mat for fitness and stretching', 'Sports', 699.00, 35, 'https://placehold.co/600x600?text=Yoga+Mat'),
('Dumbbell Set', 'Adjustable dumbbell set for strength training at home', 'Sports', 1999.00, 15, 'https://placehold.co/600x600?text=Dumbbells'),
('Cricket Bat', 'Professional quality cricket bat for outdoor sports', 'Sports', 1799.00, 12, 'https://placehold.co/600x600?text=Cricket+Bat'),
('Football', 'Durable football suitable for outdoor training and matches', 'Sports', 899.00, 25, 'https://placehold.co/600x600?text=Football'),

('Atomic Habits', 'Self improvement book about building good habits and breaking bad ones', 'Books', 499.00, 30, 'https://placehold.co/600x600?text=Atomic+Habits'),
('Rich Dad Poor Dad', 'Personal finance book about money management and investing', 'Books', 399.00, 25, 'https://placehold.co/600x600?text=Rich+Dad+Poor+Dad'),
('The Alchemist', 'Inspirational fiction novel about dreams and personal journeys', 'Books', 299.00, 20, 'https://placehold.co/600x600?text=The+Alchemist')

) AS v(name, description, category, price, stock, image_url)
WHERE NOT EXISTS (
    SELECT 1
    FROM products p
    WHERE LOWER(p.name) = LOWER(v.name)
);