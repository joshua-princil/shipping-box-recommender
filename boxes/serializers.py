from rest_framework import serializers

from .models import Box, Order, OrderItem, Product


class ProductSerializer(serializers.ModelSerializer):
    volume_cm3 = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "sku", "name",
            "length_cm", "width_cm", "height_cm", "weight_kg",
            "volume_cm3",
        ]


class BoxSerializer(serializers.ModelSerializer):
    internal_volume_cm3 = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Box
        fields = [
            "id", "code", "name",
            "internal_length_cm", "internal_width_cm", "internal_height_cm",
            "max_weight_kg", "cost", "is_active",
            "internal_volume_cm3",
        ]


class OrderItemInputSerializer(serializers.Serializer):
    """Used when creating an order: reference a product by SKU + quantity."""
    sku = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_sku(self, value):
        if not Product.objects.filter(sku=value).exists():
            raise serializers.ValidationError(f"No product with SKU '{value}'.")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    item_inputs = OrderItemInputSerializer(many=True, write_only=True)
    recommended_box = BoxSerializer(read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name="order-detail", lookup_url_kwarg="order_id")
    recommend_box_url = serializers.HyperlinkedIdentityField(
        view_name="order-recommend-box", lookup_url_kwarg="order_id"
    )

    class Meta:
        model = Order
        fields = [
            "id", "url", "order_number", "customer_name", "created_at",
            "items", "item_inputs", "recommended_box", "recommend_box_url",
        ]
        read_only_fields = ["created_at", "recommended_box"]

    def create(self, validated_data):
        item_inputs = validated_data.pop("item_inputs")
        order = Order.objects.create(**validated_data)
        products_by_sku = {p.sku: p for p in Product.objects.filter(
            sku__in=[i["sku"] for i in item_inputs]
        )}
        OrderItem.objects.bulk_create([
            OrderItem(order=order, product=products_by_sku[i["sku"]], quantity=i["quantity"])
            for i in item_inputs
        ])
        return order


class BoxRecommendationSerializer(serializers.Serializer):
    """Output shape for a single ranked box recommendation."""
    box = BoxSerializer()
    total_weight_kg = serializers.DecimalField(max_digits=10, decimal_places=3)
    total_volume_cm3 = serializers.DecimalField(max_digits=14, decimal_places=2)
    weight_utilization_pct = serializers.DecimalField(max_digits=6, decimal_places=1)
    volume_utilization_pct = serializers.DecimalField(max_digits=6, decimal_places=1)
