from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /home/
    url(r'^param_input/$', views.param_input, name='index'),
    # ex: /home/test
    url(r'^test_results/$', views.test_results, name='test')
]