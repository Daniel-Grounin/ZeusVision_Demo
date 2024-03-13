from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Initializes the auth groups for a new connection.'

    def handle(self, *args, **kwargs):
        group_names = ['drone_operator', 'control_room_operator', 'manager']

        for group_name in group_names:
            if not Group.objects.filter(name=group_name).exists():
                Group.objects.create(name=group_name)
                self.stdout.write(self.style.SUCCESS(f'Successfully created group "{group_name}"'))
            else:
                self.stdout.write(self.style.WARNING(f'Group "{group_name}" already exists'))
