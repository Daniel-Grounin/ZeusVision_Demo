from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from .models import Task
from django.core.cache import cache
from datetime import datetime


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
        cache.set('detections_test_video.mp4', [{'class': 'tank', 'confidence': 0.9}])
        response = self.client.get(reverse('video_upload'), {'video': 'detections_test_video.mp4'})
        self.assertEqual(response.status_code, 200)
