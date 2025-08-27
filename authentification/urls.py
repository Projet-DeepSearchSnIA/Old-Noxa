from django.urls import path, include
from . import views

app_name = 'authentification'

urlpatterns = [
    path('register/', views.register, name='signUp'),
    path('login/', views.loginUser, name='login'),
    path('logout/', views.logoutUser, name='logout'),
]