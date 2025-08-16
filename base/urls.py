from django.urls import path
from . import views

app_name = 'base'

urlpatterns = [
    path('', views.home, name="home"),
    path('profile/<str:pk>/', views.userProfile, name="user-profile"),
    path("collections/create/", views.createCollection, name="create-collection"),
    path('delete-collection/<str:pk>/', views.deleteCollection, name="delete-collection"),
    path('add-to-collection/<str:pk>/', views.addToCollection, name='add-to-collection'),
    path('delete-from-collection/<str:collection_id>/<str:publication_id>/', views.deleteFromCollection, name="delete-from-collection"),
    path('publication/<str:pk>/', views.publication, name="publication"),
    path('profile/<str:pk_u>/collection/<str:pk_c>/', views.collection, name="collection"),
    path('filter-topics/', views.filterTopics, name="filter-topics"),
    path('filter-authors/', views.filterAuthors, name="filter-authors"),
    path('filter-tags/', views.filterTags, name="filter-tags"),
    path('create-publication/', views.createPublication, name="create-publication"),
    path('pdf/<str:pk>/', views.viewPdf, name="pdf"),
    path('add-topic-to-fav/<str:pk>/', views.addTopicToFav, name="add-topic-to-fav"),
    path('remove-topic-from-fav/<str:pk>/', views.removeTopicFromFav, name="remove-topic-from-fav"),
]