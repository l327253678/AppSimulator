# coding=utf-8
from django.conf.urls import patterns, url
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page

from .views import (
    DashBoardView
)

from .restAPI import (
    HubXPathViewAPI, getDeviceInfoAPI, getResultSampleAPI,
    setDeviceGPSAPI, restartDeviceAPI, runScriptAPI, quitAppAPI,
    getDeviceCaptureAPI, getProxyServerInfoAPI
)

cache_time_out = 60 * 3

urlpatterns = patterns('',
                       url(r'^dashboard/$', DashBoardView.as_view(), name='dashboard'),
                       url(r'^getDeviceInfoAPI/$', getDeviceInfoAPI, name='getDeviceInfoAPI'),
                       url(r'^getResultSampleAPI/$', getResultSampleAPI, name='getResultSampleAPI'),

                       url(r'^setDeviceGPSAPI/$', setDeviceGPSAPI, name='setDeviceGPSAPI'),
                       url(r'^restartDeviceAPI/$', restartDeviceAPI, name='restartDeviceAPI'),
                       url(r'^runScriptAPI/$', runScriptAPI, name='runScriptAPI'),
                       url(r'^quitAppAPI/$', quitAppAPI, name='quitAppAPI'),

                       url(r'^getDeviceCaptureAPI/$', getDeviceCaptureAPI, name='getDeviceCaptureAPI'),
                       url(r'^getProxyServerInfoAPI/$', getProxyServerInfoAPI, name='getProxyServerInfoAPI'),
                       )
