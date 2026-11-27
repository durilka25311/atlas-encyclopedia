from django.urls import path

from . import views

app_name = 'encyclopedia'
urlpatterns = [
    path('', views.index, name='index'),
    path('article/<slug:slug>/', views.article_detail, name='article'),
    path('random/', views.random_article, name='random'),
    path('preferences/', views.preferences, name='preferences'),
]
