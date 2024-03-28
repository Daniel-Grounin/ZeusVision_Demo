from django.conf import settings
from django.core.cache import cache

def cfg_assets_root(request):

    return { 'ASSETS_ROOT' : settings.ASSETS_ROOT }

def notifications(request):
    detections = cache.get('detections', [])
    # Filter for 'tank' detections or adapt as needed
    tank_detections = [d for d in detections if d.get('class') == 'tank']
    return {'notifications': tank_detections}