"""doab_check URL Configuration
"""
from django.contrib import admin
from django.urls import path, re_path
from django.views.generic.base import TemplateView

from . import views

urlpatterns = [
    path('', views.HomepageView.as_view(), name='home'),
    path('admin/', admin.site.urls),
    path('fixing/', TemplateView.as_view(template_name='fixing.html'), name='fixing'),
    path('api/help/', TemplateView.as_view(template_name='api.html'), name='apihelp'),
    path('problems/publishers/', views.ProblemPublishersView.as_view(), name='probpubs'),
    path('problems/<str:code>/', views.ProblemsView.as_view(), name='problems'),
    path('providers/', views.ProvidersView.as_view(), name='providers'),
    path('providers/<str:provider>/', views.ProviderView.as_view(), name='provider'),
    path('publishers/', views.PublishersView.as_view(), name='publishers'),
    re_path(r'publishers/(?P<publisher>.*)', views.PublisherView.as_view(), name='publisher'),
    re_path(r'link/(?P<link_id>\d*)', views.LinkView.as_view(), name='link'),
    re_path(r'api/doab/(?P<doab>.*)', views.link_api_view, name='link_api'),

]
