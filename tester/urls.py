from django.conf.urls import url

from . import views

app_name = 'tester'

urlpatterns = [
    # ex: /home/
    url(r'^param_input/$', views.param_input, name='param_input'),
    # ex: /home/test
    url(r'^test_results/$', views.test_results, name='test_results')
]