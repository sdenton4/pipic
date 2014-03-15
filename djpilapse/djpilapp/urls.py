from django.conf.urls import patterns, url

from djpilapp import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url('^shoot/(\d+)/(\d+)/$', views.shoot, name='shoot'),
    url('^newProject/$', views.newProject, name='newProject'),
    url('^overview/$', views.overview, name='overview'),
    url('^findinitialparams/$', views.findinitialparams, name='findinitialparams'),
    url('^jsonupdate/$', views.jsonupdate, name='jsonupdate'),
)
