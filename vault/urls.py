from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("documents/", views.document_list, name="document_list"),
    path("documents/upload/", views.upload, name="upload"),
    path("documents/<int:pk>/", views.document_detail, name="document_detail"),
    path("documents/<int:pk>/download/", views.download, name="download"),
    path("documents/<int:pk>/edit/", views.edit, name="edit"),
    path("documents/<int:pk>/delete/", views.delete, name="delete"),
    path("documents/<int:pk>/share/", views.share, name="share"),
    path("documents/<int:pk>/revoke/<int:grant_id>/", views.revoke, name="revoke"),
    path("audit/", views.audit, name="audit"),
]