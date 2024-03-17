from django.conf import settings

def cfg_assets_root(request):

    return { 'ASSETS_ROOT' : settings.ASSETS_ROOT }


def user_groups(request):
    # If the user is authenticated, fetch their groups
    if request.user.is_authenticated:
        group_names = [group.name for group in request.user.groups.all()]
    else:
        group_names = []

    return {'group_names': group_names}