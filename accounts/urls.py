from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('logout/', views.logout_customer, name='logout_customer'),
    path('preferences/', views.update_preferences, name='update_preferences'),
    path('session/', views.session_status, name='session_status'),
    path('wishlist/', views.add_to_wishlist, name='add_to_wishlist'),
]
