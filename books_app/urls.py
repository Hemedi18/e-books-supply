from django.urls import path
from . import views

app_name = 'books_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.home, name='home'), # Alias for start_url
    path('request/', views.request_book, name='request_book'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('community-requests/', views.all_requests_view, name='all_requests'),
    path('upload-book/', views.upload_book_view, name='upload_book'),
    path('upload-book/for-request/<int:request_id>/', views.upload_book_view, name='upload_for_request'),
    path('about/', views.about, name='about'),
    path('help/', views.help, name='help'),
    path('contact/', views.contact, name='contact'),
    path('account/', views.account, name='account'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]