from django.conf.urls import patterns, url

from djpilapp import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url('^shoot/(\d+)/(\d+)/$', views.shoot, name='shoot'),
    url('^findinitialparams/$', views.findinitialparams, name='findinitialparams'),
    url('^jsonupdate/$', views.jsonupdate, name='jsonupdate'),
    url('^newProjectSubmit/$', views.newProjectSubmit, name='newProjectSubmit'),
)
