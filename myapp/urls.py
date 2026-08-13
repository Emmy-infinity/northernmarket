from django.urls import path
from . import views


urlpatterns = [
    
    
   
    path("notes/", views.NoteListCreate.as_view(), name="note-list"),
    path("notes/delete/<int:pk>/", views.NoteDelete.as_view(), name="note-delete"),
    path('sensor_reading/' ,views.ChartDataView.as_view()),
    path('upload/', views.ImageUploadView.as_view(), name='image-upload'),
    path('images/', views.ImageListView.as_view(), name='image-list'),
    
  

]







