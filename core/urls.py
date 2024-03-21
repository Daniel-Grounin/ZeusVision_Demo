# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib import admin
from django.urls import path, include  # add this

import apps.home.views

urlpatterns = [
    # ADD NEW Routes HERE
    path('admin/', admin.site.urls),          # Django admin route
    path("", include("apps.authentication.urls")), # Auth routes - login / register
    path('video_feed', apps.home.views.video_feed, name='video_feed'),


    # Leave `Home.Urls` as last the last line
    path("", include("apps.home.urls")),
]
