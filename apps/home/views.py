# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
import os
import cv2


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


from django.shortcuts import render
import cv2
from yolo_engine import video_detection
from django.http import StreamingHttpResponse

frame_counter = 0

# Create a directory to save the frames if it doesn't exist
save_directory = 'frames'
os.makedirs(save_directory, exist_ok=True)


def generate_frames_webcam(path_x):
    # YOLO processing code
    cap = cv2.VideoCapture(path_x)

    while True:
        success, frame = cap.read()

        if not success:
            break

        # Perform YOLO object detection on the frame
        yolo_output = video_detection(frame)

        # Convert the detected frame to JPEG format
        _, buffer = cv2.imencode('.jpg', yolo_output)
        frame_bytes = buffer.tobytes()

        # Yield the frame in the format required for multipart/x-mixed-replace
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    # Release the video capture object when done
    cap.release()

def webcam(request):
    # Use StreamingHttpResponse to send the video frames as a stream
    response = HttpResponse(generate_frames_webcam(0), content_type="multipart/x-mixed-replace; boundary=frame")

    return response