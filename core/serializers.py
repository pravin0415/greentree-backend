from rest_framework import serializers
from .models import Category, Product, Order, OrderItem
import uuid

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """Validate category name"""
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long")
        return value


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'category', 'category_name', 'name', 'description',
            'price', 'stock_quantity', 'status', 'tags', 'is_available',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_available']
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value
    
    def validate_stock_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock quantity cannot be negative")
        return value
    
    def create(self, validated_data):
        # Set default status if not provided
        if 'status' not in validated_data:
            validated_data['status'] = 'active'
        return super().create(validated_data)


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', read_only=True, max_digits=10, decimal_places=2)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_price', 'quantity', 'unit_price', 'subtotal']
        read_only_fields = ['id', 'subtotal']
    
    def validate(self, data):
        # Ensure unit_price matches product price if product is provided
        if 'product' in data and 'unit_price' in data:
            if data['unit_price'] != data['product'].price:
                raise serializers.ValidationError({
                    'unit_price': f"Unit price must match product price (${data['product'].price})"
                })
        
        # Calculate subtotal
        if 'quantity' in data and 'unit_price' in data:
            data['subtotal'] = data['quantity'] * data['unit_price']
        
        return data


class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, required=False)
    customer_email = serializers.EmailField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer_name', 'customer_email',
            'customer_phone', 'order_items', 'total_amount', 'status',
            'payment_status', 'shipping_address', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'order_number', 'created_at', 'updated_at']
    
    def validate_total_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Total amount must be greater than 0")
        return value
    
    def create(self, validated_data):
        order_items_data = validated_data.pop('order_items', [])
        order = Order.objects.create(**validated_data)
        
        # Create order items
        for item_data in order_items_data:
            OrderItem.objects.create(order=order, **item_data)
        
        return order
    
    def update(self, instance, validated_data):
        order_items_data = validated_data.pop('order_items', None)
        
        # Update order fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update order items if provided
        if order_items_data is not None:
            # Clear existing items
            instance.order_items.all().delete()
            
            # Create new items
            for item_data in order_items_data:
                OrderItem.objects.create(order=instance, **item_data)
        
        return instance


class OrderDetailSerializer(OrderSerializer):
    """Extended serializer for order details with full product info"""
    order_items = OrderItemSerializer(many=True, read_only=True)