from django.shortcuts import render, HttpResponse
from .models import BookAvailable 

# Create your views here.

def home(request):
    books = BookAvailable.objects.all()
    return render(request, 'books_app/home.html', {'books': books})

def request_book(request):
    return HttpResponse('<h1> this feature is coming soon </h1>')

def about(request):
    return HttpResponse('<h1> this feature is coming soon </h1>')

def help(request):
    return HttpResponse('<h1> this feature is coming soon </h1>')

def contact(request):
    return HttpResponse('<h1> this feature is coming soon </h1>')

def account(request):   
    return HttpResponse('<h1> this feature is coming soon </h1>')

