from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /home/
    url(r'^$', views.index, name='index'),
    # ex: /home/test
    url(r'^test/$', views.test, name='test')
]