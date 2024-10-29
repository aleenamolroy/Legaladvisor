# your_app_name/routing.py

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/chat/<int:client_id>/<int:advocate_id>/', consumers.ChatConsumer.as_asgi(), name='chat'),
]
