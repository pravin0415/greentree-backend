from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import uuid

class Category(models.Model):
    """
    Product Category Model
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Model validation"""
        if not self.name:
            raise ValidationError({'name': 'Category name is required'})
        if len(self.name) > 100:
            raise ValidationError({'name': 'Category name cannot exceed 100 characters'})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Product Model with foreign key to Category
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('discontinued', 'Discontinued'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='products'
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    stock_quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active'
    )
    tags = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['category', 'status']),
        ]
    
    def __str__(self):
        return f"{self.name} - ${self.price}"
    
    def clean(self):
        """Model validation"""
        if not self.name:
            raise ValidationError({'name': 'Product name is required'})
        if self.price < 0:
            raise ValidationError({'price': 'Price cannot be negative'})
        if self.stock_quantity < 0:
            raise ValidationError({'stock_quantity': 'Stock quantity cannot be negative'})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_available(self):
        return self.status == 'active' and self.stock_quantity > 0


class Order(models.Model):
    """
    Order Model with ManyToMany relationship to Product
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # ManyToMany relationship with Products
    products = models.ManyToManyField(
        Product, 
        through='OrderItem',
        related_name='orders'
    )
    
    total_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='pending'
    )
    shipping_address = models.TextField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['customer_email']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number} - {self.customer_name}"
    
    def clean(self):
        """Model validation"""
        if not self.customer_name:
            raise ValidationError({'customer_name': 'Customer name is required'})
        if not self.customer_email:
            raise ValidationError({'customer_email': 'Customer email is required'})
        if self.total_amount < 0:
            raise ValidationError({'total_amount': 'Total amount cannot be negative'})
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number on first save
            last_order = Order.objects.order_by('-created_at').first()
            if last_order and last_order.order_number:
                last_num = int(last_order.order_number.split('-')[1])
                new_num = last_num + 1
            else:
                new_num = 1001
            self.order_number = f"ORD-{new_num:06d}"
        
        self.full_clean()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """
    Intermediate model for Order-Product ManyToMany relationship
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        unique_together = ['order', 'product']
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def clean(self):
        """Model validation"""
        if self.quantity < 1:
            raise ValidationError({'quantity': 'Quantity must be at least 1'})
        if self.unit_price < 0:
            raise ValidationError({'unit_price': 'Unit price cannot be negative'})
        if self.subtotal != self.quantity * self.unit_price:
            raise ValidationError({'subtotal': 'Subtotal must equal quantity * unit_price'})
    
    def save(self, *args, **kwargs):
        # Auto-calculate subtotal if not set
        if not self.subtotal:
            self.subtotal = self.quantity * self.unit_price
        self.full_clean()
        super().save(*args, **kwargs)