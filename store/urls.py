from django.urls import path

from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('currency/', views.set_currency, name='set_currency'),
]
