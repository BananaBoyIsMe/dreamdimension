from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('stories/', views.story_list, name='story_list'),
    path('stories/new/', views.story_create, name='story_create'),
    path('stories/<slug:slug>/', views.story_detail, name='story_detail'),
    path('users/<str:username>/', views.profile, name='profile'),
    path('stories/<slug:slug>/chapters/new/', views.chapter_create, name='chapter_create'),
    path('stories/<slug:slug>/chapters/<int:pk>/', views.chapter_detail, name='chapter_detail'),
    path('reviews/add/<slug:story_slug>/', views.review_create, name='review_create'),
    path('reviews/edit/<int:review_id>/', views.review_edit, name='review_edit'),
    path('reviews/delete/<int:review_id>/', views.review_delete, name='review_delete'),
    path("account/update/", views.account_update, name="account_update"),
    path("account/delete/", views.account_delete, name="account_delete"),
    path("account/password/", auth_views.PasswordChangeView.as_view(template_name="dreambooks/password_change.html"), name="password_change"),
    path('stories/<slug:slug>/chapters/<int:pk>/edit/', views.chapter_edit, name='chapter_edit'),
    path('stories/<slug:slug>/chapters/<int:pk>/delete/', views.chapter_delete, name='chapter_delete'),
    path('stories/<slug:slug>/edit/', views.story_edit, name='story_edit'),
    # path('contact/', views.contact, name='contact'),
    path("contact/", views.contact_list_create, name="contact"),
    path("contact/<int:pk>/edit/", views.contact_edit, name="contact_edit"),
    path("contact/<int:pk>/delete/", views.contact_delete, name="contact_delete"),
    path('about/', views.about, name='about'),
]