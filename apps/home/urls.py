# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path, include
from apps.home import views


urlpatterns = [

    # The home page
    path('', views.index, name='home'),
    path('map/', views.map_view, name='map'),
    path('webcam/', views.webcam_view, name='webcam'),
    path('video_upload/', views.video_upload_view, name='video_upload'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('test/', views.test_view, name='test'),
    path('user/', views.user_view, name='user'),
    # path('api/drone-location', views.receive_drone_location, name='receive_drone_location'),






    # Matches any html file
    # re_path(r'^.*\.*', views.pages, name='pages'),
    # path('video_feed', views.video_feed, name='video_feed'),



]
