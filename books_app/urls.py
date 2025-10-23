from django.urls import path
from . import views

app_name = 'books_app'

urlpatterns = [
    path('', views.login_view, name='login'), # Login is now the root page
    path('dashboard/', views.home, name='home'), # The book list is now the dashboard

    # Auth routes
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    path('requestbook/', views.request_book, name='request_book'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('about/', views.about, name="about"),
    path('help/', views.help, name="help"),
    path('contact/', views.contact, name="contact"),
    path('account/', views.account, name="account"),
]