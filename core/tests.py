from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Category, Product, Order
import decimal

class CategoryModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Test Category",
            description="Test Description"
        )
    
    def test_category_creation(self):
        self.assertEqual(self.category.name, "Test Category")
        self.assertEqual(str(self.category), "Test Category")
    
    def test_category_validation(self):
        # Test name validation
        category = Category(name="")
        with self.assertRaises(Exception):
            category.full_clean()
    
    def test_verbose_name_plural(self):
        self.assertEqual(str(Category._meta.verbose_name_plural), "Categories")


class ProductModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            category=self.category,
            name="Test Product",
            description="Test Description",
            price=decimal.Decimal("99.99"),
            stock_quantity=10
        )
    
    def test_product_creation(self):
        self.assertEqual(self.product.name, "Test Product")
        self.assertEqual(self.product.price, decimal.Decimal("99.99"))
        self.assertTrue(self.product.is_available)
    
    def test_product_unavailable(self):
        product = Product.objects.create(
            category=self.category,
            name="Out of Stock",
            description="Test",
            price=decimal.Decimal("10.00"),
            stock_quantity=0,
            status="active"
        )
        self.assertFalse(product.is_available)


class OrderModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test")
        self.product = Product.objects.create(
            category=self.category,
            name="Test Product",
            description="Test",
            price=decimal.Decimal("50.00"),
            stock_quantity=10
        )
        
        self.order = Order.objects.create(
            customer_name="John Doe",
            customer_email="john@example.com",
            total_amount=decimal.Decimal("100.00"),
            shipping_address="123 Test St"
        )
    
    def test_order_creation(self):
        self.assertEqual(self.order.customer_name, "John Doe")
        self.assertTrue(self.order.order_number.startswith("ORD-"))
    
    def test_order_validation(self):
        order = Order(
            customer_name="",
            customer_email="",
            total_amount=decimal.Decimal("-10.00"),
            shipping_address="Test"
        )
        with self.assertRaises(Exception):
            order.full_clean()


class CategoryAPITests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Test Category",
            description="Test Description"
        )
        self.url = reverse('category-list')
    
    def test_get_categories(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_category(self):
        data = {
            "name": "New Category",
            "description": "New Description"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 2)


class ProductAPITests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            category=self.category,
            name="Test Product",
            description="Test",
            price=decimal.Decimal("99.99"),
            stock_quantity=10
        )
        self.url = reverse('product-list')
    
    def test_get_products(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_products(self):
        response = self.client.get(f'{self.url}?category={self.category.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_search_products(self):
        response = self.client.get(f'{self.url}?search=Test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class OrderAPITests(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test")
        self.product = Product.objects.create(
            category=self.category,
            name="Test Product",
            description="Test",
            price=decimal.Decimal("50.00"),
            stock_quantity=10
        )
        
        self.order = Order.objects.create(
            customer_name="John Doe",
            customer_email="john@example.com",
            total_amount=decimal.Decimal("100.00"),
            shipping_address="123 Test St"
        )
        self.url = reverse('order-list')
    
    def test_get_orders(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_by_status(self):
        response = self.client.get(f'{self.url}?status=pending')
        self.assertEqual(response.status_code, status.HTTP_200_OK)