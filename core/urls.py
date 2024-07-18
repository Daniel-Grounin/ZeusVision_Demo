# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.contrib import admin
from django.urls import path, include  # add this
from django.conf import settings
from django.conf.urls.static import static
import apps.home.views

urlpatterns = [
    # ADD NEW Routes HERE
    path('admin/', admin.site.urls),          # Django admin route
    path("", include("apps.authentication.urls")), # Auth routes - login / register
    path('first_webcam_feed', apps.home.views.first_webcam_feed, name='first_webcam_feed'),
    path('second_webcam_feed', apps.home.views.second_webcam_feed, name='second_webcam_feed'),
    path('get_processing_progress/', apps.home.views.get_processing_progress, name='get_processing_progress'),

    # Leave `Home.Urls` as last the last line
    path("", include("apps.home.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)