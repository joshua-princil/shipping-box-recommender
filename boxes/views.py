from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from .models import Box, Order, Product
from .serializers import (
    BoxRecommendationSerializer,
    BoxSerializer,
    OrderSerializer,
    ProductSerializer,
)
from .services import NoSuitableBoxError, get_ranked_candidate_boxes, recommend_box


@api_view(["GET"])
def api_root(request, format=None):
    """
    Landing page for the API. Visiting this in a browser (rather than curl)
    renders DRF's browsable API: a clickable HTML page, so you can navigate
    from here into products/boxes/orders without knowing the URLs upfront.
    """
    return Response({
        "products": reverse("product-list", request=request, format=format),
        "boxes": reverse("box-list", request=request, format=format),
        "orders": reverse("order-list", request=request, format=format),
    })


class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class BoxListCreateView(generics.ListCreateAPIView):
    queryset = Box.objects.all()
    serializer_class = BoxSerializer


class OrderListCreateView(generics.ListCreateAPIView):
    queryset = Order.objects.prefetch_related("items__product")
    serializer_class = OrderSerializer


class OrderDetailView(generics.RetrieveAPIView):
    queryset = Order.objects.prefetch_related("items__product")
    serializer_class = OrderSerializer


class RecommendBoxView(APIView):
    """
    GET  /api/orders/<id>/recommend-box/            -> best recommendation, saved on the order
    GET  /api/orders/<id>/recommend-box/?all=true    -> every viable box, cheapest first
    """

    def get(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id)

        try:
            if request.query_params.get("all", "").lower() == "true":
                candidates = get_ranked_candidate_boxes(order)
                data = BoxRecommendationSerializer(candidates, many=True).data
                return Response({"order": order.order_number, "candidates": data})

            best = recommend_box(order, persist=True)
            data = BoxRecommendationSerializer(best).data
            return Response({"order": order.order_number, "recommendation": data})

        except NoSuitableBoxError as exc:
            return Response(
                {
                    "order": order.order_number,
                    "error": str(exc),
                    "total_weight_kg": exc.total_weight_kg,
                    "total_volume_cm3": exc.total_volume_cm3,
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
