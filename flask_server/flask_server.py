import json

from flask import Flask, request, Response
from flask_api import status

from device_manager.DeviceManager import DeviceManager
from logger.logger import get_logger
from storage.Device import Device

logger = get_logger(__name__)

def create_app():
    app = Flask(__name__)
    deviceManager = DeviceManager()

    @app.route('/scan')
    def scan():
        return deviceManager.scan_devices()

    @app.route('/')
    def get_devices():
        devices = deviceManager.get_devices()
        if devices.count == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(json.dumps([json.loads(str(d)) for d in devices]), content_type='application/json')

    @app.route('/devices/<mac>', methods=['GET'])
    def get_device(mac: str):
        device = deviceManager.get_device(mac)
        if device is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return json.loads(str(device))

    @app.route('/devices', methods=['POST'])
    def add_device():
        args = request.args
        mac = args.get('mac')
        device = deviceManager.add_device(mac)
        if not isinstance(device, Device):
            return Response(str(device), status=status.HTTP_400_BAD_REQUEST)
        return json.loads(str(device)), status.HTTP_201_CREATED

    @app.route('/devices/<mac>', methods=['DELETE'])
    def delete_device(mac: str):
        device = deviceManager.get_device(mac)
        if device is not None:
            if deviceManager.delete_device(device):
                return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @app.route('/devices/online', methods=['GET'])
    def get_online_device():
        devices = deviceManager.get_online_devices()
        if devices.count == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(json.dumps([json.loads(str(d)) for d in devices]), content_type='application/json')

    @app.route('/devices/<mac>/statistics', methods=['GET'])
    def get_device_statistics(mac: str):
        device = deviceManager.get_device(mac)
        if device is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        stat_data = deviceManager._get_stat(device)
        if not stat_data:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        # Convert stat_data to a proper response format
        response_data = [
            {
                "timestamp": d[0],
                "temperature": d[3],
                "humidity": d[4],
                "battery": d[5]
            }
            for d in stat_data
        ]
        return Response(json.dumps(response_data), content_type='application/json')

    return app
