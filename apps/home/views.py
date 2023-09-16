
from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
import cv2
from ultralytics import YOLO

from yolo_engine import video_detection
from django.http import StreamingHttpResponse
from django.shortcuts import render


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


yolo = YOLO('yolov8n.pt')

def draw_boxes(frame, detections):
    for detection in detections:
        x1, y1, x2, y2, class_id, conf = detection

        # Convert coordinates to integers
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Add class label and confidence score
        label = f'Class {int(class_id)}: {conf:.2f}'
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return frame


def stream():
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        # Perform object detection using YOLOv8
        detections = yolo(frame)


        # Convert the frame to JPEG format
        image_bytes = cv2.imencode('.jpg', frame)[1].tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + image_bytes + b'\r\n')


def video_feed(request):
    return StreamingHttpResponse(stream(), content_type='multipart/x-mixed-replace; boundary=frame')