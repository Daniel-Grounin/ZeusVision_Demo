from django import forms
from django.contrib.auth.models import User, Group
from .models import Task

class TaskForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        drone_operators_group = Group.objects.get(name='drone_operator')
        self.fields['assigned_to'].queryset = drone_operators_group.user_set.all()

    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to']