"""doab_check URL Configuration
"""
from django.contrib import admin
from django.urls import path, re_path
from django.views.generic.base import TemplateView

from . import views

urlpatterns = [
    path('', views.HomepageView.as_view(), name='home'),
    path('admin/', admin.site.urls),
    path('problems/', views.ProblemsView.as_view(), name='problems'),
    path('providers/', views.ProvidersView.as_view(), name='providers'),
    path('providers/<str:provider>/', views.ProviderView.as_view(), name='provider'),
    path('publishers/', views.PublishersView.as_view(), name='publishers'),
    re_path(r'publishers/(?P<publisher>.*)', views.PublisherView.as_view(), name='publisher'),
]
