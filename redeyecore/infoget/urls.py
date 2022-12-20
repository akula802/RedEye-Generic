# app-level urls.py

# Core library imports

# 3rd-party imports
from django.urls import path, include
from django.contrib.auth import views as auth_views

# Local app imports
from . import views



urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('api/', include('api.urls')),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
]
