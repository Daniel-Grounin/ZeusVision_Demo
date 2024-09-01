from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.core.cache import cache
from datetime import datetime

from .forms import TaskForm, VideoUploadForm
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Task



class ViewsTestCase(TestCase):

    def setUp(self):
        self.client = Client()

        # Create necessary groups
        self.manager_group = Group.objects.create(name='manager')
        self.operator_group = Group.objects.create(name='control_room_operator')
        self.drone_operator_group = Group.objects.create(name='drone_operator')

        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.user.groups.add(self.operator_group)
        self.client.login(username='testuser', password='testpassword')

        # Create Task object and add user to many-to-many field
        self.task = Task.objects.create(title='Test Task', description='Test Description')
        self.task.assigned_to.set([self.user])

    def test_manager_access(self):
        self.user.groups.clear()
        self.user.groups.add(self.manager_group)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/index.html')

    def test_operator_access(self):
        self.user.groups.clear()
        self.user.groups.add(self.operator_group)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/index.html')

    def test_drone_operator_access(self):
        self.user.groups.clear()
        self.user.groups.add(self.drone_operator_group)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/index.html')


    def test_index_view_get(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/index.html')

    def test_index_view_post_create_task(self):
        response = self.client.post(reverse('home'), {
            'action': 'create_task',
            'title': 'New Task',
            'description': 'New Description'
        })
        self.assertEqual(response.status_code, 200)  # Redirect after creating task
        self.assertFalse(Task.objects.filter(title='New Task').exists())

    def test_index_view_post_delete_task(self):
        response = self.client.post(reverse('home'), {
            'action': 'delete_task',
            'task_id': self.task.id
        })
        self.assertEqual(response.status_code, 302)  # Redirect after deleting task
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())

    def test_index_view_post_start_mission(self):
        response = self.client.post(reverse('home'), {
            'action': 'start_mission',
            'task_id': self.task.id
        })
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertTrue(self.client.session['active_mission']['task_id'], str(self.task.id))

    def test_index_view_post_stop_mission(self):
        response = self.client.post(reverse('home'), {
            'action': 'stop_mission',
            'task_id': self.task.id
        })
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.id, 1)
        self.assertNotIn('active_mission', self.client.session)



    def test_first_webcam_feed_view(self):
        response = self.client.get(reverse('first_webcam_feed'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'multipart/x-mixed-replace; boundary=frame')

    def test_second_webcam_feed_view(self):
        response = self.client.get(reverse('second_webcam_feed'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'multipart/x-mixed-replace; boundary=frame')

    def test_map2_view(self):
        cache.set('drone_location', (10.0, 20.0))
        cache.set('drone_messages', ['Test message'])
        response = self.client.get(reverse('map'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/map_mapbox.html')
        self.assertContains(response, '10.0')
        self.assertContains(response, '20.0')
        self.assertContains(response, 'Test message')

    def test_webcam_view(self):
        response = self.client.get(reverse('webcam'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/webcam.html')

    def test_video_upload_view_get(self):
        response = self.client.get(reverse('video_upload'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/newvideoupload.html')

    def test_notifications_view(self):
        response = self.client.get(reverse('notifications'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/notifications.html')

    def test_create_task_with_long_title(self):
        long_title = 'A' * 256  # Assuming 255 is the max length
        response = self.client.post(reverse('home'), {
            'action': 'create_task',
            'title': long_title,
            'description': 'Long title description'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(title=long_title).exists())

    def test_create_task_with_missing_fields(self):
        response = self.client.post(reverse('home'), {
            'action': 'create_task',
            'title': '',
            'description': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(description='').exists())

    def test_delete_task_when_no_tasks_exist(self):
        Task.objects.all().delete()  # Ensure no tasks exist
        response = self.client.post(reverse('home'), {
            'action': 'delete_task',
            'task_id': 1
        })
        self.assertEqual(response.status_code, 404)

    def test_start_mission_when_mission_already_active(self):
        self.client.post(reverse('home'), {
            'action': 'start_mission',
            'task_id': self.task.id
        })
        response = self.client.post(reverse('home'), {
            'action': 'start_mission',
            'task_id': self.task.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('active_mission', self.client.session)

    def test_stop_mission_that_does_not_exist(self):
        response = self.client.post(reverse('home'), {
            'action': 'stop_mission',
            'task_id': 999  # Non-existent task
        })
        self.assertEqual(response.status_code, 404)

    def test_task_form_valid_data(self):
        user = User.objects.create_user(username='testuser2', password='testpassword')
        user.groups.add(self.drone_operator_group)  # Ensure the user belongs to the correct group
        form_data = {
            'title': 'Test Task',
            'description': 'This is a test task.',
            'assigned_to': [user.id],
        }
        form = TaskForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_task_form_missing_title(self):
        form_data = {
            'title': '',
            'description': 'Missing title.',
            'assigned_to': [self.user.id],
        }
        form = TaskForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_task_form_missing_assigned_to(self):
        form_data = {
            'title': 'Task without Assignee',
            'description': 'No user assigned.',
        }
        form = TaskForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('assigned_to', form.errors)

    def test_task_form_queryset_manager(self):
        self.user.groups.clear()
        manager_group = Group.objects.get(name='manager')
        self.user.groups.add(manager_group)

        form = TaskForm(user=self.user)
        self.assertQuerysetEqual(
            form.fields['assigned_to'].queryset,
            User.objects.filter(groups__name__in=['control_room_operator', 'drone_operator']).distinct(),
            transform=lambda x: x
        )

    def test_task_form_queryset_control_room_operator(self):
        self.user.groups.clear()
        operator_group = Group.objects.get(name='control_room_operator')
        self.user.groups.add(operator_group)

        form = TaskForm(user=self.user)
        self.assertQuerysetEqual(
            form.fields['assigned_to'].queryset,
            User.objects.filter(groups__name='drone_operator'),
            transform=lambda x: x
        )

    from django.core.files.uploadedfile import SimpleUploadedFile

    def test_video_upload_form_valid_file(self):
        video_file = SimpleUploadedFile("media/5.mp4", b"file_content", content_type="video/mp4")
        form = VideoUploadForm(files={'video': video_file})
        self.assertTrue(form.is_valid())

    def test_video_upload_form_invalid_file(self):
        invalid_file = SimpleUploadedFile("test.txt", b"not a video", content_type="text/plain")
        form = VideoUploadForm(files={'video': invalid_file})
        self.assertFalse(form.is_valid())
        self.assertIn('video', form.errors)

    def test_video_upload_form_empty_file(self):
        empty_file = SimpleUploadedFile("empty.mp4", b"", content_type="video/mp4")
        form = VideoUploadForm(files={'video': empty_file})
        self.assertFalse(form.is_valid())
        self.assertIn('video', form.errors)
    def test_task_form_queryset_neither_manager_nor_operator(self):
        self.user.groups.clear()

        form = TaskForm(user=self.user)
        self.assertFalse(form.fields['assigned_to'].queryset.exists())

    def test_user_view(self):
        response = self.client.get(reverse('user'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/user.html')
        self.assertContains(response, 'testuser')

    def test_get_drone_location_view(self):
        cache.set('drone_location', (10.0, 20.0))
        response = self.client.get(reverse('get_drone_location'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'latitude': 10.0, 'longitude': 20.0})

    def test_get_drone_messages_view(self):
        cache.set('drone_messages', ['Test message'])
        response = self.client.get(reverse('get_drone_messages'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'messages': ['Test message']})

    def test_get_processing_progress_view(self):
        cache.set('video_processing_progress', 50)
        response = self.client.get(reverse('get_processing_progress'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'progress': 50})

    def test_get_detections_view(self):
        cache.set('media/1.mp4', [{'class': 'tank', 'confidence': 0.9}])
        response = self.client.get(reverse('video_upload'), {'video': 'media/1.mp4'})
        self.assertEqual(response.status_code, 200)

    def test_video_upload_with_invalid_format(self):
        with open('test.txt', 'w') as f:
            f.write("This is not a video file.")
        with open('test.txt', 'rb') as invalid_file:
            response = self.client.post(reverse('video_upload'), {'video': invalid_file})
        self.assertEqual(response.status_code, 200)

    def test_process_video_with_no_detectable_objects(self):
        response = self.client.post(reverse('video_upload'), {'video': 'media/1.mp4'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'detections')

    def test_cache_cleared_on_task_delete(self):
        cache.set('drone_location', (10.0, 20.0))
        self.client.post(reverse('home'), {
            'action': 'delete_task',
            'task_id': self.task.id
        })
        self.assertIsNotNone(cache.get('drone_location'))

    def test_cache_update_on_mission_start(self):
        self.client.post(reverse('home'), {
            'action': 'start_mission',
            'task_id': self.task.id
        })
        self.assertIn('active_mission', self.client.session)
        self.assertEqual(self.client.session['active_mission']['task_id'], str(self.task.id))

    def test_handle_empty_rtsp_stream(self):
        response = self.client.get(reverse('second_webcam_feed'), {'model': 'yolov8n.pt'})
        self.assertEqual(response.status_code, 200)

    def test_handle_corrupt_video_file(self):
        with open('corrupt.mp4', 'wb') as f:
            f.write(b'\x00\x00\x00\x00')
        with open('corrupt.mp4', 'rb') as corrupt_file:
            response = self.client.post(reverse('video_upload'), {'video': corrupt_file})
        self.assertEqual(response.status_code, 200)


    def test_task_form_validation(self):
        response = self.client.post(reverse('home'), {
            'action': 'create_task',
            'title': '',
            'description': 'Task without a title'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(description='Task without a title').exists())

    def test_csrf_protection(self):
        response = self.client.post(reverse('home'), {
            'action': 'create_task',
            'title': 'CSRF Test Task',
            'description': 'Testing CSRF protection'
        }, follow=True)
        self.assertNotEqual(response.status_code, 403)

    def test_session_management(self):
        self.client.post(reverse('home'), {
            'action': 'start_mission',
            'task_id': self.task.id
        })
        self.assertIn('active_mission', self.client.session)
        self.client.post(reverse('home'), {
            'action': 'stop_mission',
            'task_id': self.task.id
        })
        self.assertNotIn('active_mission', self.client.session)

def test_process_corrupted_video(self):
    with self.assertLogs('django.request', level='ERROR') as cm:
        corrupted_file = SimpleUploadedFile("corrupt.mp4", b"\x00\x00\x00\x00", content_type="video/mp4")
        response = self.client.post(reverse('video_upload'), {'video': corrupted_file})
        self.assertContains(response, "moov atom not found")
