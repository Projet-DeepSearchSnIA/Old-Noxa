from django.urls import path, include
from . import views

app_name = 'authentification'

urlpatterns = [
    path('', views.signUp_view, name='signUp'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
]