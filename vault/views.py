from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from .models import Document

def home(request):
    return render(request, 'vault/home.html')

def signup(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm = request.POST.get('confirm_password')
        if password != confirm:
            return render(request, 'vault/signup.html', {'error': 'Passwords do not match!'})
        if User.objects.filter(username=username).exists():
            return render(request, 'vault/signup.html', {'error': 'Username already exists!'})
        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = full_name
        user.save()
        return redirect('login')
    return render(request, 'vault/signup.html')

def login(request):
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
        return render(request, 'vault/login.html', {'error': 'Invalid username or password!'})
    return render(request, 'vault/login.html')

def forgot(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        pw = request.POST.get('password')
        confirm = request.POST.get('confirm_password')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return render(request, 'vault/forgot.html', {'error': 'Username not found!'})
        if pw != confirm:
            return render(request, 'vault/forgot.html', {'error': 'Passwords do not match!'})
        user.set_password(pw)
        user.save()
        return redirect('login')
    return render(request, 'vault/forgot.html')

def logout(request):
    auth_logout(request)
    return redirect('home')

@login_required(login_url='login')
def dashboard(request):
    search = request.GET.get('search')
    docs = Document.objects.filter(user=request.user)
    if search:
        docs = docs.filter(title__icontains=search)
    return render(request, 'vault/dashboard.html', {'documents': docs.order_by('-uploaded_at')})

@login_required(login_url='login')
def upload_document(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        file = request.FILES.get('file')
        if file:
            Document.objects.create(user=request.user, title=title, file=file)
    return redirect('dashboard')

@login_required(login_url='login')
def delete_document(request, document_id):
    if request.method == 'POST':
        d = Document.objects.get(id=document_id, user=request.user)
        d.file.delete()
        d.delete()
    return redirect('dashboard')

@login_required(login_url='login')
def profile(request):
    return render(request, 'vault/profile.html')
def about(request):
    return render(request, 'vault/about.html')
def help_page(request):
    return render(request, 'vault/help.html')