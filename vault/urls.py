from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('owner/', views.owner_dashboard, name='owner'),
    path('owner/delete/<int:doc_id>/', views.owner_delete, name='owner_delete'),
    path('viewer/', views.viewer_dashboard, name='viewer'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('about/', views.about, name='about'),
    path('help/', views.help_page, name='help'),
]