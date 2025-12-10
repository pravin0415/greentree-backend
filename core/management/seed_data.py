from django.core.management.base import BaseCommand
from core.models import Category, Product, Order, OrderItem
import decimal
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Seed the database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')
        
        # Clear existing data
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        
        # Create Categories
        categories = [
            {'name': 'Electronics', 'description': 'Electronic devices and accessories'},
            {'name': 'Books', 'description': 'Books and reading materials'},
            {'name': 'Clothing', 'description': 'Apparel and fashion items'},
            {'name': 'Home & Garden', 'description': 'Home improvement and gardening'},
            {'name': 'Sports', 'description': 'Sports equipment and gear'},
        ]
        
        category_objs = []
        for cat_data in categories:
            category = Category.objects.create(**cat_data)
            category_objs.append(category)
            self.stdout.write(f'Created category: {category.name}')
        
        # Create Products
        products = [
            {
                'name': 'Laptop Pro X1',
                'description': 'High-performance laptop with 16GB RAM, 512GB SSD',
                'price': decimal.Decimal('1299.99'),
                'stock_quantity': 25,
                'tags': 'laptop,electronics,computer',
                'category': category_objs[0],
            },
            {
                'name': 'Wireless Headphones',
                'description': 'Noise-cancelling wireless headphones',
                'price': decimal.Decimal('199.99'),
                'stock_quantity': 50,
                'tags': 'audio,headphones,wireless',
                'category': category_objs[0],
            },
            {
                'name': 'Smartphone X',
                'description': 'Latest smartphone with advanced camera',
                'price': decimal.Decimal('899.99'),
                'stock_quantity': 30,
                'tags': 'phone,mobile,smartphone',
                'category': category_objs[0],
            },
            {
                'name': 'Python Programming Book',
                'description': 'Complete guide to Python programming',
                'price': decimal.Decimal('49.99'),
                'stock_quantity': 100,
                'tags': 'book,programming,python',
                'category': category_objs[1],
            },
            {
                'name': 'Winter Jacket',
                'description': 'Waterproof winter jacket with insulation',
                'price': decimal.Decimal('129.99'),
                'stock_quantity': 40,
                'tags': 'clothing,winter,jacket',
                'category': category_objs[2],
            },
            {
                'name': 'Gardening Tool Set',
                'description': 'Complete set of gardening tools',
                'price': decimal.Decimal('79.99'),
                'stock_quantity': 60,
                'tags': 'garden,tools,home',
                'category': category_objs[3],
            },
            {
                'name': 'Yoga Mat',
                'description': 'Premium non-slip yoga mat',
                'price': decimal.Decimal('34.99'),
                'stock_quantity': 80,
                'tags': 'sports,yoga,fitness',
                'category': category_objs[4],
            },
            {
                'name': 'Desk Lamp',
                'description': 'LED desk lamp with adjustable brightness',
                'price': decimal.Decimal('29.99'),
                'stock_quantity': 120,
                'tags': 'home,office,lamp',
                'category': category_objs[3],
            },
        ]
        
        product_objs = []
        for prod_data in products:
            product = Product.objects.create(**prod_data)
            product_objs.append(product)
            self.stdout.write(f'Created product: {product.name} - ${product.price}')
        
        # Create Orders with OrderItems
        customers = [
            {'name': 'John Doe', 'email': 'john@example.com', 'phone': '123-456-7890'},
            {'name': 'Jane Smith', 'email': 'jane@example.com', 'phone': '987-654-3210'},
            {'name': 'Bob Johnson', 'email': 'bob@example.com', 'phone': '555-123-4567'},
            {'name': 'Alice Brown', 'email': 'alice@example.com', 'phone': '444-555-6666'},
        ]
        
        order_statuses = ['pending', 'processing', 'shipped', 'delivered']
        payment_statuses = ['pending', 'paid', 'paid', 'paid']
        
        for i, customer in enumerate(customers):
            # Create order with past dates for variety
            order_date = datetime.now() - timedelta(days=random.randint(1, 30))
            
            order = Order.objects.create(
                customer_name=customer['name'],
                customer_email=customer['email'],
                customer_phone=customer['phone'],
                total_amount=decimal.Decimal('0.00'),
                status=random.choice(order_statuses),
                payment_status=random.choice(payment_statuses),
                shipping_address=f'{random.randint(100, 999)} Main St, City, State {random.randint(10000, 99999)}',
                notes='Thank you for your order!' if i % 2 == 0 else ''
            )
            
            # Manually set created_at to simulate past orders
            order.created_at = order_date
            order.save()
            
            # Add 1-3 random products to order
            num_items = random.randint(1, 3)
            selected_products = random.sample(product_objs, num_items)
            
            total_amount = decimal.Decimal('0.00')
            
            for product in selected_products:
                quantity = random.randint(1, 3)
                subtotal = product.price * quantity
                total_amount += subtotal
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=product.price,
                    subtotal=subtotal
                )
            
            # Update order total
            order.total_amount = total_amount
            order.save()
            
            self.stdout.write(f'Created order: {order.order_number} for {order.customer_name} - ${order.total_amount}')
        
        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))
        
        # Display summary
        self.stdout.write('\n📊 Database Summary:')
        self.stdout.write(f'  Categories: {Category.objects.count()}')
        self.stdout.write(f'  Products: {Product.objects.count()}')
        self.stdout.write(f'  Orders: {Order.objects.count()}')
        self.stdout.write(f'  Order Items: {OrderItem.objects.count()}')