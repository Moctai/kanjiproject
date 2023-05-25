from django.urls import path
from . import views

app_name = 'kanjiapp'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('word/<int:p>', views.WordView.as_view(), name='word'),
    path('result', views.ResultView.as_view(), name='result'),
    path('source', views.SourceView.as_view(), name='source'),
    path('disclaimer', views.DisclaimerView.as_view(), name='disclaimer'),
    path('tags', views.TagsView.as_view(), name='tags'),
]