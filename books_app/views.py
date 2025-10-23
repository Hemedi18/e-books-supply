from django.shortcuts import render, HttpResponse, redirect
from .models import BookAvailable, RequesterProfile, BookRequest
from .forms import (
    BookRequestForm, MyRequestsForm, CustomUserCreationForm, 
    UserUpdateForm, ProfileUpdateForm
)
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# Create your views here.

@login_required
def home(request):
    books = BookAvailable.objects.all()
    return render(request, 'books_app/home.html', {'books': books})

@login_required
def request_book(request):
    if request.method == 'POST':
        form = BookRequestForm(request.POST)
        if form.is_valid():
            # Since the user is logged in, we can get their profile directly.
            book_request = form.save(commit=False)
            book_request.requester = request.user.requesterprofile
            book_request.save()
            
            messages.success(request, f"Your request for '{book_request.book_title}' has been submitted!")
            return redirect('books_app:my_requests')
    else:
        form = BookRequestForm()

    return render(request, 'books_app/request_book.html', {'form': form})

@login_required
def my_requests(request):
    form = MyRequestsForm(request.GET or None)
    requests_list = []
    if form.is_valid():
        whatsapp_number = form.cleaned_data['whatsapp_number']
        requests_list = BookRequest.objects.filter(requester__whatsapp_number=whatsapp_number).order_by('-request_date')

    return render(request, 'books_app/my_requests.html', {'form': form, 'requests_list': requests_list})

@login_required
def about(request):
    # The user's provided GitHub URL was corrected for accessibility.
    github_url = "https://github.com/Hemedi18/e-books-supply"
    return render(request, 'books_app/about.html', {'github_url': github_url})

@login_required
def help(request):
    return HttpResponse('<h1> this feature is coming soon </h1>')

@login_required
def contact(request):
    contact_info = {
        'phone': '+255678260396',
        'email': 'supplyebooks.tz@gmail.com',
    }
    return render(request, 'books_app/contact.html', {'contact': contact_info})

@login_required
def account(request):
    # Ensure a profile exists for the user, creating one if it doesn't.
    # This makes the view robust for any user, including superusers.
    profile, created = RequesterProfile.objects.get_or_create(
        user=request.user,
        defaults={'whatsapp_name': request.user.username} # Provide a default name
    )

    if request.method == 'POST':
        # Initialize all forms to ensure they exist in the context
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)
        password_form = PasswordChangeForm(request.user)

        # Check which form is being submitted
        if 'update_profile' in request.POST:
            u_form = UserUpdateForm(request.POST, instance=request.user)
            p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
            if u_form.is_valid() and p_form.is_valid():
                u_form.save()
                p_form.save()
                messages.success(request, 'Your account has been updated!')
                return redirect('books_app:account')
        
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Important to keep the user logged in
                messages.success(request, 'Your password was successfully updated!')
                return redirect('books_app:account')
            else:
                messages.error(request, 'Please correct the password errors below.')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)
        password_form = PasswordChangeForm(request.user)
    return render(request, 'books_app/account.html', {'u_form': u_form, 'p_form': p_form, 'password_form': password_form})


# --- Authentication Views ---

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            # Render a success page that will redirect to login
            return render(request, 'books_app/signup_done.html') # This path is correct
    else:
        form = CustomUserCreationForm()
    return render(request, 'books_app/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            return redirect('books_app:home')
    else:
        form = AuthenticationForm()
    return render(request, 'books_app/login.html', {'form': form}) # This path is also correct

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, "You have been successfully logged out.")
        return redirect('books_app:login')
    # If accessed via GET, show a confirmation page.
    return render(request, 'books_app/logout.html')
