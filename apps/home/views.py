import socket
from datetime import datetime
from django.core.cache import cache

from urllib import request

from django import template
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
import cv2
from django.views.decorators.http import require_POST
from pyexpat.errors import messages

# from .models import YoloData
from ultralytics import YOLO

import yolo_engine
from yolo_engine import video_detection
from django.http import StreamingHttpResponse
from django.shortcuts import render, get_object_or_404

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.decorators import login_required

# Import the server socket class
from .ServerSocket import run_server
from . import ServerSocket


yolo_data_str = []

@login_required
def index(request):
    is_manager = request.user.groups.filter(name='manager').exists()
    is_control_room_operator = request.user.groups.filter(name='control_room_operator').exists()
    is_drone_operator = request.user.groups.filter(name='drone_operator').exists()  # Check if user is a drone operator

    if is_manager:
        tasks = Task.objects.all()
    else:
        tasks = Task.objects.filter(assigned_to=request.user)

    mission_status = False  # Initialize mission status to False
    drone_name = ""  # Initialize drone name to an empty string

    if request.method == 'POST':
        if request.POST.get('action') == 'delete_task':

            # Handle task deletion
            task_id = request.POST.get('task_id')
            task = get_object_or_404(Task, id=task_id)

            # Check if the task being deleted is the active mission
            if 'active_mission' in request.session and request.session['active_mission']['task_id'] == str(task.id):
                del request.session['active_mission']
            # Proceed with deletion
            task.delete()
            # messages.success(request, "Task deleted successfully.")
            return redirect('home')  # Redirect to the same view to refresh the tasks list
        elif request.POST.get('action') == 'start_mission':
            # Handle starting mission
            task_id = request.POST.get('task_id')
            # Add your mission start logic here
            # For example, you can update the task status to indicate that the mission has started
            task = get_object_or_404(Task, id=task_id)
            task.status = 'In Progress'
            task.save()
            # Set mission_status to True when mission starts
            mission_status = True
            # Set drone_name (example: "UAV 1")
            drone_name = "UAV 1"  # Change this to the actual drone name
            request.session['active_mission'] = {
                'task_id': task_id,
                'status': 'In Progress',
                'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Store start time
            }
        elif request.POST.get('action') == 'stop_mission':
            # Handle stopping mission
            task_id = request.POST.get('task_id')
            task = get_object_or_404(Task, id=task_id)
            task.status = 'Stopped'
            task.save()
            # Clear the active mission from the session if it's the one being stopped
            if 'active_mission' in request.session and request.session['active_mission']['task_id'] == task_id:
                del request.session['active_mission']
        else:
            # Handle task creation
            form = TaskForm(request.POST, user=request.user)
            if form.is_valid():
                task = form.save(commit=False)
                # Optionally set any additional task attributes here
                task.save()
                form.save_m2m()  # Save many-to-many relationships, like assigned_to
                # messages.success(request, "Task created successfully.")
                return redirect('home')

    form = TaskForm(user=request.user)  # Pass user to form for custom queryset in assigned_to
    detections = cache.get('detections', [])
    context = {
        'tasks': tasks,
        'is_manager': is_manager,
        'is_control_room_operator': is_control_room_operator,
        'is_drone_operator': is_drone_operator,
        'mission_status': mission_status,
        'drone_name': drone_name,
        'form': form,
        'detections': detections,
    }

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

FRAME_SKIP_FACTOR = 2
def generate_frames_webcam(path_x, model_name):
    print(f"Connecting to RTSP URL: {path_x} using model: {model_name}")
    cap = cv2.VideoCapture(path_x)

    # Reduce buffer size
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print(f"Unable to open video source {path_x}")
        return

    frame_count = 0
    while cap.isOpened():
        success, frame = cap.read()
        frame_count += 1

        if not success:
            print("Failed to read frame")
            break

        if frame is None or frame.size == 0:
            print("Empty frame received")
            continue

        # Skip every fifth frame
        if frame_count % FRAME_SKIP_FACTOR == 0:
            continue

        # Always resize the frame to a smaller resolution
        frame = cv2.resize(frame, (640, 640))

        # Process frame using the selected YOLO model
        frame = video_detection(frame, model_name)

        # Encode frame to JPEG
        ref, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()


def first_webcam_feed(request):
    model_name = request.GET.get('model', 'yolov8n.pt')  # Default to yolov8n.pt
    url_address = "192.168.1.148"
    rtsp_url = f"rtsp://user:pass@{url_address}:8554/streaming/live/1"
    return StreamingHttpResponse(generate_frames_webcam(rtsp_url, model_name), content_type='multipart/x-mixed-replace; boundary=frame')

def second_webcam_feed(request):
    model_name = request.GET.get('model', 'yolov8n.pt')  # Default to yolov8n.pt
    return StreamingHttpResponse(generate_frames_webcam(path_x=1, model_name=model_name), content_type='multipart/x-mixed-replace; boundary=frame')

@login_required
def map2_view(request):
    # Retrieve the latest drone location from the cache
    drone_location = cache.get('drone_location', (0.0, 0.0))  # Default to (0.0, 0.0) if no data
    drone_messages = cache.get('drone_messages', [])  # Retrieve messages from cache
    context = {
        'drone_location': drone_location,
        'drone_messages': drone_messages
    }
    return render(request, 'home/map_mapbox.html', context)

@login_required
def webcam_view(request):
    # You can add context variables to pass to the template as needed
    context = {}
    # Render and return the index.html template
    return render(request, 'home/webcam.html', context)

@login_required
def notifications_view(request):
    # You can add context variables to pass to the template as needed
    context = {}
    # Render and return the index.html template
    return render(request, 'home/notifications.html', context)


@login_required
def user_view(request):
    # request.user contains the currently logged-in user
    user = request.user

    # Pass the user details to the template
    return render(request, 'home/user.html', {'user': user})



from django.shortcuts import render
from .models import Task
from django.contrib.auth.decorators import login_required


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import TaskForm

def is_manager(user):
    return user.groups.filter(name='manager').exists()



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def get_drone_location(request):
    if request.method == 'GET':
        # Retrieve the latest drone location from the cache
        drone_location = cache.get('drone_location', (0.0, 0.0))  # Default to (0.0, 0.0) if no data
        return JsonResponse({
            'latitude': drone_location[0],
            'longitude': drone_location[1]
        })
    else:
        return JsonResponse({"status": "error", "message": "Only GET requests are allowed"}, status=405)



def get_drone_messages(request):
    if request.method == 'GET':
        # Retrieve the latest drone messages from wherever they are stored
        drone_messages = cache.get('drone_messages', [])  # Assume messages are stored in cache
        return JsonResponse({'messages': drone_messages})
    else:
        return JsonResponse({"status": "error", "message": "Only GET requests are allowed"}, status=405)
#run_server()




import os
import cv2
import math
from datetime import datetime
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
from .forms import VideoUploadForm
from ultralytics import YOLO
from django.http import JsonResponse
from django.core.cache import cache


def video_upload_view(request):
    global video_files
    if request.method == 'POST':
        form = VideoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            video_file = form.cleaned_data['video']
            fs = FileSystemStorage()
            filename = fs.save(video_file.name, video_file)
            video_length = get_video_length(fs.path(filename))  # Get video length
            request.session['video_length'] = video_length  # Store video length in session
            processed_file_url = process_video(fs.path(filename), fs, request)
            detections = extract_detections(processed_file_url)
            generate_thumbnails(fs.location)  # Generate thumbnails
            video_files = get_video_files(fs.location)
            return render(request, 'home/newvideoupload.html', {
                'form': form,
                'processed_file_url': processed_file_url,
                'detections': detections,
                'video_files': video_files,
            })
    else:
        form = VideoUploadForm()
        fs = FileSystemStorage()
        generate_thumbnails(fs.location)  # Generate thumbnails
        video_files = get_video_files(fs.location)
    return render(request, 'home/newvideoupload.html', {'form': form, 'video_files': video_files})


def get_video_length(video_path):
    cap = cv2.VideoCapture(video_path)
    length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return length


def process_video(video_path, fs, request):
    # Check if this video has already been processed
    if cache.get(f'processed_{video_path}'):
        print(f"Video {video_path} has already been processed.")
        return cache.get(f'processed_url_{video_path}')

    cap = cv2.VideoCapture(video_path)
    model = YOLO("../ZeusVision_Demo/best3.pt")
    classNames = ["tank"]
    detections = []

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    output_path = video_path.replace('.mp4', '_processed.mp4')

    # Ensure the file name is unique if needed
    if os.path.exists(output_path):
        output_path = video_path.replace('.mp4', f'_processed_{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.mp4')

    # Use H.264 codec (which is widely supported in browsers) and MP4 container
    fourcc = cv2.VideoWriter.fourcc(*'avc1')  # H.264 codec
    out = cv2.VideoWriter(output_path, fourcc, 10, (frame_width, frame_height))

    video_length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # Get the total number of frames
    processed_frames = 0

    while cap.isOpened():
        success, img = cap.read()
        if not success:
            break

        # Perform YOLO detection on the given frame
        results = model(img, stream=True)

        for r in results:
            for box in r.boxes:
                # Extract coordinates and ensure they are within the frame dimensions
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                # Ensure the coordinates are within the frame boundaries
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(img.shape[1], x2), min(img.shape[0], y2)

                conf = box.conf[0]
                cls = int(box.cls[0])
                class_name = classNames[cls]

                if conf >= 0.6:
                    cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 2)
                    label = f'{class_name} {conf:.2f}'
                    t_size = cv2.getTextSize(label, 0, fontScale=0.5, thickness=1)[0]
                    c2 = x1 + t_size[0], y1 - t_size[1] - 3
                    cv2.rectangle(img, (x1, y1), c2, [255, 0, 255], -1, cv2.LINE_AA)  # filled
                    cv2.putText(img, label, (x1, y1 - 2), 0, 0.5, [255, 255, 255], thickness=1, lineType=cv2.LINE_AA)

                    if class_name == 'tank':
                        detections.append({'class': 'Tank', 'confidence': conf,
                                           'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

        out.write(img)
        processed_frames += 1
        progress = int((processed_frames / video_length) * 100)
        cache.set('video_processing_progress', progress)  # Store progress in cache

    cap.release()
    out.release()

    # Save processed video
    with open(output_path, 'rb') as f:
        filename = fs.save(output_path.split('/')[-1], f)
    cache.set(f'detections_{filename}', detections)  # Cache detections for this video
    processed_url = fs.url(filename)
    cache.set(f'processed_url_{video_path}', processed_url)  # Cache the URL of the processed video
    cache.set(f'processed_{video_path}', True)  # Mark this video as processed
    return processed_url



def extract_detections(processed_video_url):
    return []


def get_video_files(media_root):
    video_extensions = ['.mp4', '.avi', '.mov']
    video_files = []
    for root, dirs, files in os.walk(media_root):
        for file in files:
            if any(file.endswith(ext) for ext in video_extensions):
                video_files.append(os.path.join(root, file))
    return [os.path.basename(video) for video in video_files]


def generate_thumbnails(media_root):
    video_extensions = ['.mp4', '.avi', '.mov']
    thumbnail_dir = os.path.join(media_root, 'thumbnails')
    os.makedirs(thumbnail_dir, exist_ok=True)

    for root, dirs, files in os.walk(media_root):
        for file in files:
            if any(file.endswith(ext) for ext in video_extensions):
                video_path = os.path.join(root, file)
                thumbnail_path = os.path.join(thumbnail_dir, f'{os.path.splitext(file)[0]}.png')

                if not os.path.exists(thumbnail_path):
                    cap = cv2.VideoCapture(video_path)
                    success, frame = cap.read()
                    if success:
                        cv2.imwrite(thumbnail_path, frame)
                    cap.release()


def get_processing_progress(request):
    progress = cache.get('video_processing_progress', 0)
    return JsonResponse({'progress': progress})


def get_detections(request):
    video = request.GET.get('video')
    detections = cache.get(f'detections_{video}', [])
    return JsonResponse({'detections': detections})
