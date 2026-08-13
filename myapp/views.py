from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny


from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Note, SensorReading, Photo, StockMarketReading
from .serializers import (
    SensorReadingSerializer, 
    UserSerializer, 
    NoteSerializer, 
    PhotoSerializer
)



#  PASTE THIS INSTEAD:
from rest_framework import viewsets, permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Product, Photo
from .serializers import ProductSerializer, PhotoSerializer

class ProductViewSet(viewsets.ModelViewSet):
    """
    Handles listing, creating, retrieving, updating, and deleting products.
    """
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    # Class-based viewsets use the property directly without an import wrapper!
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)


class PhotoViewSet(viewsets.ModelViewSet):
    """
    Handles uploading images and linking them to specific products.
    """
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    # MultiPartParser handles your incoming React image binaries perfectly
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        product_id = self.request.data.get('product')
        if product_id:
            try:
                product = Product.objects.get(id=product_id)
                serializer.save(product=product)
            except Product.DoesNotExist:
                serializer.save()
        else:
            serializer.save()





class NoteListCreate(generics.ListCreateAPIView):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Note.objects.filter(author=user)

    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save(author=self.request.user)
        else:
            print(serializer.errors)


class NoteDelete(generics.DestroyAPIView):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Note.objects.filter(author=user)


class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class ChartDataView2(APIView):
    def get(self, request):
        readings = StockMarketReading.objects.all().order_by('timestamp')
        x = [r.timestamp.strftime('%Y-%m-%d %H:%M:%S') for r in readings]
        y1 = [r.value1 for r in readings]
        y2 = [r.value2 for r in readings]
        chart_data = {
            "data": [
                {
                    "x": x,
                    "y": y1,
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Stock Value 1",
                },
                {
                    "x": x,
                    "y": y2,
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Stock Value 2",
                }
            ],
            "layout": {
                "title": "Stock Market Reading",
                "xaxis": {"title": "Time"},
                "yaxis": {"title": "Value"},
            }
        }
        return Response(chart_data)


class ChartDataView(APIView):
    def get(self, request):
        readings = SensorReading.objects.all().order_by('timestamp')
        x = [r.timestamp.strftime('%Y-%m-%d %H:%M:%S') for r in readings]
        y = [r.value for r in readings]

        chart_data = {
            "data": [
                {
                    "x": x,
                    "y": y,
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Sensor",
                }
            ],
            "layout": {
                "title": "Sensor Data",
                "xaxis": {"title": "Time"},
                "yaxis": {"title": "Value"},
            }
        }
        return Response(chart_data)


# Cloudinary Photo Endpoints
class ImageListView(generics.ListAPIView):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [AllowAny]


class ImageUploadView(generics.CreateAPIView):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    parser_classes = (MultiPartParser, FormParser)  # Required to handle image binaries
    permission_classes = [AllowAny]
