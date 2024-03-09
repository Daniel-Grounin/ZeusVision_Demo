from urllib import request

from django import template
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
import cv2
# from .models import YoloData
from yolo_engine import data_from_yolo
from ultralytics import YOLO

import yolo_engine
from yolo_engine import video_detection
from django.http import StreamingHttpResponse
from django.shortcuts import render

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from .models import DroneLocation

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from django.shortcuts import render
from django.contrib.auth.decorators import login_required




yolo_data_str = []
@login_required(login_url="/login/")
def index(request):
    # You can add context variables to pass to the template as needed
    context = {}
    # Render and return the index.html template
    return render(request, 'home/index.html', context)



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






def video_feed(request):
    return StreamingHttpResponse(generate_frames_webcam(path_x=0), content_type='multipart/x-mixed-replace; boundary=frame')
    # return StreamingHttpResponse(generate_frames_webcam(path_x="rtmp://172.19.32.178:1935/live"), content_type='multipart/x-mixed-replace; boundary=frame')


def map_view(request):
    # You can add context variables to pass to the template as needed
    context = {}
    # Render and return the index.html template
    return render(request, 'home/map.html', context)


def webcam_view(request):
    # You can add context variables to pass to the template as needed
    context = {}
    # Render and return the index.html template
    return render(request, 'home/webcam.html', context)


def video_upload_view(request):
    # You can add context variables to pass to the template as needed
    context = {}
    # Render and return the index.html template
    return render(request, 'home/newvideoupload.html', context)


def notifications_view(request):
    # You can add context variables to pass to the template as needed
    context = {}
    # Render and return the index.html template
    return render(request, 'home/notifications.html', context)


def test_view(request):
    context = {}
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            altitude = data.get('altitude')
            # Process the data, for example, save it to the database or log it.
            print('*****')
            print(latitude)
            # Print success message to terminal
            print("Success: Received drone location data.")

            print(JsonResponse({'status': 'success'}, status=200))
            return render(request, 'home/test.html', context)
        except Exception as e:
            print(JsonResponse({'status': 'error', 'message': str(e)}, status=400))
    return render(request, 'home/test.html', context)


def user_view(request):
    # request.user contains the currently logged-in user
    user = request.user

    # Pass the user details to the template
    return render(request, 'home/user.html', {'user': user})



