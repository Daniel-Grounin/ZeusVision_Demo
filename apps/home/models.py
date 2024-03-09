# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.db import models
from django.contrib.auth.models import User
class YoloData(models.Model):
    #user only save 1 number not primay key
    user=models
    yolo_data= models.CharField(max_length=1000)
    date= models.DateTimeField(auto_now_add=True)



