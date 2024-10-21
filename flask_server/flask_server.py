import json

from flask import Flask, request, Response
from flask_api import status

from tinker_soft.embeddings.DeviceManager import DeviceManager
from logger.logger import get_logger
from storage.Device import Device

logger = get_logger(__name__)

def create_app():
    app = Flask(__name__)
    embeddings = DeviceManager()

    @app.route('/scan')
    def scan():
        return embeddings.scan_devices()

    @app.route('/')
    def get_devices():
        devices = embeddings.get_devices()
        if devices.count == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(json.dumps([json.loads(str(d)) for d in devices]), content_type='application/json')

    @app.route('/devices/<mac>', methods=['GET'])
    def get_device(mac: str):
        device = embeddings.get_device(mac)
        if device is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return json.loads(str(device))

    @app.route('/devices', methods=['POST'])
    def add_device():
        args = request.args
        mac = args.get('mac')
        device = embeddings.add_device(mac)
        if not isinstance(device, Device):
            return Response(str(device), status=status.HTTP_400_BAD_REQUEST)
        return json.loads(str(device)), status.HTTP_201_CREATED

    @app.route('/devices/<mac>', methods=['DELETE'])
    def delete_device(mac: str):
        device = embeddings.get_device(mac)
        if device is not None:
            if embeddings.delete_device(device):
                return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @app.route('/devices/online', methods=['GET'])
    def get_online_device():
        devices = embeddings.get_online_devices()
        if devices.count == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(json.dumps([json.loads(str(d)) for d in devices]), content_type='application/json')

    return app
