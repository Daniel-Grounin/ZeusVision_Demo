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



def generate_frames_webcam(path_x):
    print(f"Connecting to RTSP URL: {path_x}")
    cap = cv2.VideoCapture(path_x)

    if not cap.isOpened():
        print(f"Unable to open video source {path_x}")
        return

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Failed to read frame")
            break

        if frame is None or frame.size == 0:
            print("Empty frame received")
            continue

        # Process frame if needed (e.g., using YOLO)
        # Uncomment and use if you have a video_detection function
        # yolo_output = video_detection(frame)

        # Encode frame to JPEG
        ref, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()




def video_feed(request):
    return StreamingHttpResponse(generate_frames_webcam(path_x=2), content_type='multipart/x-mixed-replace; boundary=frame')
    #return StreamingHttpResponse(generate_frames_webcam(path_x="rtmp://192.168.137.1:1935/live"), content_type='multipart/x-mixed-replace; boundary=frame')

def first_webcam_feed(request):
    return StreamingHttpResponse(generate_frames_webcam(path_x=1), content_type='multipart/x-mixed-replace; boundary=frame')
    #return StreamingHttpResponse(generate_frames_webcam(path_x="rtmp://192.168.137.1:1935/live"), content_type='multipart/x-mixed-replace; boundary=frame')

def second_webcam_feed(request):
    rtsp_url = "rtsp://user:pass@192.168.137.239:8554/streaming/live/1"
    # return StreamingHttpResponse(generate_frames_webcam(path_x=2), content_type='multipart/x-mixed-replace; boundary=frame')
    return StreamingHttpResponse(generate_frames_webcam(rtsp_url), content_type='multipart/x-mixed-replace; boundary=frame')

def third_webcam_feed(request):
    rtsp_url = "rtsp://user:pass@192.168.137.157:1935/live"
    return StreamingHttpResponse(generate_frames_webcam(path_x=3), content_type='multipart/x-mixed-replace; boundary=frame')
    # return StreamingHttpResponse(generate_frames_webcam(path_x="rtmp://172.19.32.178:1935/live"), content_type='multipart/x-mixed-replace; boundary=frame')



def map2_view(request):
    # Retrieve the latest drone location from the cache
    drone_location = cache.get('drone_location', (0.0, 0.0))  # Default to (0.0, 0.0) if no data
    context = {'drone_location': drone_location}
    return render(request, 'home/map_mapbox.html', context)

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




#run_server()