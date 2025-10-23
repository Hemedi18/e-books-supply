from django.urls import path
from . import views

app_name = 'books_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('requestbook/', views.request_book, name='request_book'),
    path('about/', views.about, name="about"),
    path('help/', views.help, name="help"),
    path('contact/', views.contact, name="contact"),
    path('account/', views.account, name="account"),


]