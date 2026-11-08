from django.urls import path
from . import views
urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('forgot/', views.forgot, name='forgot'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/', views.upload_document, name='upload'),
    path('profile/', views.profile, name='profile'),
    path('delete/<int:document_id>/', views.delete_document, name='delete_document'),
    path('about/', views.about, name='about'),
    path('help/', views.help_page, name='help'),
]