from django.contrib import admin

from .models import Box, Order, OrderItem, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "length_cm", "width_cm", "height_cm", "weight_kg")
    search_fields = ("sku", "name")


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "internal_length_cm", "internal_width_cm",
                     "internal_height_cm", "max_weight_kg", "cost", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer_name", "recommended_box", "created_at")
    inlines = [OrderItemInline]
    readonly_fields = ("recommended_box",)
