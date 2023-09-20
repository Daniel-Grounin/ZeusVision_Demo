from urllib import request

from django import template
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
import cv2
from .models import YoloData
from yolo_engine import data_from_yolo
from ultralytics import YOLO

import yolo_engine
from yolo_engine import video_detection
from django.http import StreamingHttpResponse
from django.shortcuts import render

yolo_data_str = []
@login_required(login_url="/login/")
def index(request):
    context = {'segment': 'index'}

    html_template = loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:

        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))



def generate_frames_webcam(path_x):
    yolo_output = video_detection(path_x)
    for detection_ in yolo_output:
        ref, buffer = cv2.imencode('.jpg', detection_)
        frame = buffer.tobytes()
        yolo_data_str=','.join(map(str,data_from_yolo))
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        SaveYoloData(yolo_data_str)



def SaveYoloData(yolo_data_str):
    user = User.objects.get(username='dori')
    yolo_data = YoloData(user=user, yolo_data=yolo_data_str)
    yolo_data.save()
    print("yolo_data_str",yolo_data_str)
    print("yolo_data",yolo_data)

#def sort_yolo_data(yolo_data_str):


def video_feed(request):
    return StreamingHttpResponse(generate_frames_webcam(path_x=0), content_type='multipart/x-mixed-replace; boundary=frame')
    # return StreamingHttpResponse(generate_frames_webcam(path_x="rtmp://172.1.100.70:1935"), content_type='multipart/x-mixed-replace; boundary=frame')

