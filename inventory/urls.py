from django.urls import path

from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('medicines/', views.medicine_list, name='medicine_list'),
    path('medicines/add/', views.medicine_create, name='medicine_create'),
    path('medicines/<int:pk>/edit/', views.medicine_update, name='medicine_update'),
    path('medicines/<int:pk>/delete/', views.medicine_delete, name='medicine_delete'),
    path('suppliers/', views.supplier_list, name='supplier_list'),
]