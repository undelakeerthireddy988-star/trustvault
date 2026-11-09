from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Document

# 1. HOME PAGE CHUPINCHADANIKI
def home(request):
    return render(request, 'vault/home.html')

# 2. SIGNUP - Get Started click chesthe ikkada vasthundi
def signup_view(request):
    error = ""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role', '').lower()

        if User.objects.filter(username=username).exists():
            error = "Username already exists. Please Login."
        elif len(password) < 4:
            error = "Password min 4 characters undali."
        else:
            user = User.objects.create_user(username=username, password=password)
            user.groups.clear()
            if role == 'admin':
                user.is_superuser = True
                user.is_staff = True
                user.save()
                login(request, user)
                return redirect('/admin-dashboard/')
            elif role == 'owner':
                g, _ = Group.objects.get_or_create(name='Owner')
                user.groups.add(g)
                login(request, user)
                return redirect('/owner/')
            else:
                g, _ = Group.objects.get_or_create(name='Viewer')
                user.groups.add(g)
                login(request, user)
                return redirect('/viewer/')
    return render(request, 'vault/signup.html', {'error': error})

# 3. LOGIN - Role check chesi pampisthundi
def login_view(request):
    error = ""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')
        user = authenticate(request, username=username, password=password)
        if user is None:
            error = "Invalid username or password."
        elif role == 'owner' and not user.groups.filter(name='Owner').exists():
            error = "You are not an Owner."
        elif role == 'viewer' and not user.groups.filter(name='Viewer').exists():
            error = "You are not a Viewer."
        elif role == 'admin' and not user.is_superuser:
            error = "You are not an Admin."
        else:
            login(request, user)
            if role == 'owner':
                return redirect('/owner/')
            if role == 'viewer':
                return redirect('/viewer/')
            if role == 'admin':
                return redirect('/admin-dashboard/')
    return render(request, 'vault/login.html', {'error': error})

# 4. LOGOUT
def logout_view(request):
    logout(request)
    return redirect('/')

# 5. OWNER - Upload + Search + Delete
@login_required(login_url='/login/')
def owner_dashboard(request):
    q = request.GET.get('q', '')
    docs = Document.objects.filter(owner=request.user)
    if q:
        docs = docs.filter(title__icontains=q)
    if request.method == 'POST':
        title = request.POST.get('title')
        file = request.FILES.get('file')
        if title and file:
            Document.objects.create(owner=request.user, title=title, file=file)
            return redirect('/owner/')
    return render(request, 'vault/owner.html', {'docs': docs, 'q': q})

@login_required(login_url='/login/')
def owner_delete(request, doc_id):
    doc = Document.objects.filter(id=doc_id, owner=request.user).first()
    if doc:
        doc.delete()
    return redirect('/owner/')

# 6. VIEWER - Only Search
@login_required(login_url='/login/')
def viewer_dashboard(request):
    q = request.GET.get('q', '')
    docs = Document.objects.all()
    if q:
        docs = docs.filter(title__icontains=q)
    return render(request, 'vault/viewer.html', {'docs': docs, 'q': q})

# 7. ADMIN - All Users + All Docs
@login_required(login_url='/login/')
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('/login/')
    users = User.objects.all()
    docs = Document.objects.all()
    return render(request, 'vault/admin.html', {'users': users, 'docs': docs})
def about(request):
    return render(request, 'vault/about.html')

def help_page(request):
    return render(request, 'vault/help.html')