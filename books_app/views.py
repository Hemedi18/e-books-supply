from django.shortcuts import render, HttpResponse, redirect
from .models import BookAvailable, RequesterProfile, BookRequest
from .forms import (
    BookRequestForm, CustomUserCreationForm, UserUpdateForm, BookUploadForm,
    ProfileUpdateForm
)
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

# Create your views here.

@login_required
def home(request):
    queryset = BookAvailable.objects.filter(is_available=True).order_by('-published_date', 'title')
    query = request.GET.get('q')

    if query:
        # Filter by title or author, case-insensitively
        queryset = queryset.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        ).distinct()
    return render(request, 'books_app/home.html', {'books': queryset, 'query': query})

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
    # Fetch requests directly for the logged-in user.
    try:
        # Get the user's profile, which is linked to their requests.
        profile = request.user.requesterprofile
        requests_list = BookRequest.objects.filter(requester=profile).order_by('-request_date')
    except RequesterProfile.DoesNotExist:
        # This is a fallback in case a user (like a superuser) doesn't have a profile.
        requests_list = []
        messages.warning(request, "Your requester profile could not be found. Please visit your account page to ensure it's set up correctly.")
        
    return render(request, 'books_app/my_requests.html', {'requests_list': requests_list})

@login_required
def all_requests_view(request):
    """
    Displays all book requests from all users to the community.
    """
    all_requests = BookRequest.objects.all().order_by('-request_date')
    return render(request, 'books_app/all_requests.html', {'requests_list': all_requests})

@login_required
def upload_book_view(request, request_id=None):
    """
    Handles book uploads by any authenticated user.
    If a request_id is provided, it fulfills that request upon successful upload.
    """
    book_request_to_fulfill = None
    if request_id:
        try:
            book_request_to_fulfill = BookRequest.objects.get(id=request_id, status='PENDING')
        except BookRequest.DoesNotExist:
            messages.error(request, "This book request could not be found or has already been fulfilled.")
            return redirect('books_app:all_requests')

    if request.method == 'POST':
        form = BookUploadForm(request.POST, request.FILES)
        if form.is_valid():
            new_book = form.save() # The book is now in the catalog
            
            # If this upload is meant to fulfill a specific request
            if book_request_to_fulfill:
                book_request_to_fulfill.book_requested = new_book
                book_request_to_fulfill.status = 'FULFILLED'
                book_request_to_fulfill.fulfillment_date = timezone.now()
                book_request_to_fulfill.save()
                messages.success(request, f"Thank you! You have successfully uploaded '{new_book.title}' and fulfilled the request.")
                return redirect('books_app:all_requests')

            messages.success(request, f"Thank you for your contribution! '{new_book.title}' has been added to the catalog.")
            return redirect('books_app:home')
    else:
        form = BookUploadForm(initial={'title': book_request_to_fulfill.book_title if book_request_to_fulfill else '', 'author': book_request_to_fulfill.book_author if book_request_to_fulfill else ''})
    return render(request, 'books_app/upload_book.html', {'form': form, 'request_to_fulfill': book_request_to_fulfill})

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
    profile, created = RequesterProfile.objects.get_or_create(user=request.user,
        defaults={
            'whatsapp_name': request.user.username,
            'whatsapp_number': None # Explicitly set to None on creation
        }
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
