# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path, include
from apps.home import views
from core import settings
from django.conf.urls.static import static

urlpatterns = [

    # The home page
    path('', views.index, name='home'),
    path('map/', views.map2_view, name='map'),
    path('webcam/', views.webcam_view, name='webcam'),
    path('video_upload/', views.video_upload_view, name='video_upload'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('user/', views.user_view, name='user'),
    path('get_drone_location/', views.get_drone_location, name='get_drone_location'),
    path('get_drone_messages/', views.get_drone_messages, name='get_drone_messages'),
    # path('api/drone-location', views.receive_drone_location, name='receive_drone_location'),

    # Matches any html file
    # re_path(r'^.*\.*', views.pages, name='pages'),
    # path('video_feed', views.video_feed, name='video_feed'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)