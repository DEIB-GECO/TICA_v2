from django.conf.urls import url

from . import views

app_name = 'tester'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    # ex: /home/
    url(r'^param_input/$', views.param_input, name='param_input'),
    # ex: /home/test
    url(r'^test_results/$', views.test_results, name='test_results'),

    url(r'^back_to_session/$', views.back_to_session, name='back_to_session'),
    url(r'^test_results_encode/$', views.test_results_encode, name='test_results_encode'),

]