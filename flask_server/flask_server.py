import json

from flask import Flask, request, Response
from flask_api import status

from sensor_manager.SensorManager import SensorManager
from logger.logger import get_logger
from storage.Sensor import Sensor
from flask_cors import CORS
from flask import jsonify
from datetime import datetime

logger = get_logger(__name__)

def create_app():
    app = Flask(__name__)
    CORS(app)
    deviceManager = SensorManager()

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
        if not isinstance(device, Sensor):
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

    # @app.route('/devices/<mac>/statistics', methods=['GET'])
    # def get_device_statistics(mac: str):
    #     device = deviceManager.get_device(mac)
    #     if device is None:
    #         return Response(status=status.HTTP_404_NOT_FOUND)

    #     stat_data = deviceManager._get_stat(device)
    #     if not stat_data:
    #         return Response(status=status.HTTP_404_NOT_FOUND)
        
    #     # Convert stat_data to a proper response format
    #     response_data = [
    #         {
    #             "timestamp": d[0],
    #             "temperature": d[3],
    #             "humidity": d[4],
    #             "battery": d[5]
    #         }
    #         for d in stat_data
    #     ]
    #     return Response(json.dumps(response_data), content_type='application/json')


    @app.route('/devices/<mac>/statistics', methods=['GET'])
    def get_device_statistics(mac: str):
            """
            Получить статистику устройства за заданный период или за всё время.

            :param mac: MAC-адрес устройства.
            :return: JSON-ответ со статистикой.
            """
            device = deviceManager.get_device(mac)
            if device is None:
                return Response(status=404)

            # Извлечение параметров даты из строки запроса
            start_date = request.args.get('start_date')  # Формат 'YYYY-MM-DD'
            end_date = request.args.get('end_date')      # Формат 'YYYY-MM-DD'

            # Проверка формата дат
            try:
                if start_date:
                    datetime.strptime(start_date, '%Y-%m-%d')
                if end_date:
                    datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                return jsonify({"error": "Invalid date format. Use 'YYYY-MM-DD'."}), 400

            # Получение статистических данных
            stat_data = deviceManager._get_stat(device, start_date=start_date, end_date=end_date)
            if not stat_data:
                return Response(status=404)

            # Формирование ответа
            response_data = [
                {
                    "timestamp": d[2],  # Assuming 'time' is in the third column
                    "temperature": d[3],
                    "humidity": d[4],
                    "battery": d[5]
                }
                for d in stat_data
            ]
            return jsonify(response_data), 200


    return app
