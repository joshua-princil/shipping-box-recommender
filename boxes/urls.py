from django.urls import path

from . import views

urlpatterns = [
    path("", views.api_root, name="api-root"),
    path("products/", views.ProductListCreateView.as_view(), name="product-list"),
    path("boxes/", views.BoxListCreateView.as_view(), name="box-list"),
    path("orders/", views.OrderListCreateView.as_view(), name="order-list"),
    path("orders/<int:order_id>/", views.OrderDetailView.as_view(), name="order-detail"),
    path("orders/<int:order_id>/recommend-box/", views.RecommendBoxView.as_view(), name="order-recommend-box"),
]
