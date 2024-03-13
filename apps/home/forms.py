# forms.py
from django import forms
from .models import Task
from django.contrib.auth.models import User, Group


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TaskForm, self).__init__(*args, **kwargs)

        if user is not None:
            if user.groups.filter(name='manager').exists():
                # Managers can assign tasks to anyone: both control room operators and drone operators
                control_room_group = Group.objects.get(name='control_room_operator')
                drone_operator_group = Group.objects.get(name='drone_operator')
                self.fields['assigned_to'].queryset = User.objects.filter(
                    groups__in=[control_room_group, drone_operator_group]
                ).distinct()
            elif user.groups.filter(name='control_room_operator').exists():
                # Control room operators can only assign tasks to drone operators
                drone_operator_group = Group.objects.get(name='drone_operator')
                self.fields['assigned_to'].queryset = User.objects.filter(groups=drone_operator_group)
            else:
                # If it's neither a manager nor a control room operator, clear the queryset
                self.fields['assigned_to'].queryset = User.objects.none()
