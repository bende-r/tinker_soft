import subprocess
import argparse
import threading
from flask_server.flask_server import create_app
import socket
import json

import time

class DiscoveryClient:
    def __init__(self, discovery_port=5000):
        self.discovery_port = discovery_port
        self.last_registration_time = 0  # Время последней регистрации
        self.registration_interval = 60  # Интервал в секундах (1 минута)
        self.is_registered = False  # Флаг успешной регистрации

    def start(self):
        udp_thread = threading.Thread(target=self._listen_for_discovery)
        udp_thread.daemon = True
        udp_thread.start()

    def _listen_for_discovery(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', self.discovery_port))

        try:
            while not self.is_registered:  # Слушать только до успешной регистрации
                data, addr = s.recvfrom(1024)
                try:
                    message = json.loads(data.decode('utf-8'))
                    if message["type"] == "discovery":
                        current_time = time.time()
                        # Проверяем, прошёл ли интервал регистрации
                        if current_time - self.last_registration_time >= self.registration_interval:
                            self._register_with_server(addr[0], message["tcp_port"])
                            self.last_registration_time = current_time
                except Exception as e:
                    print(f"Error processing discovery message: {e}")
        finally:
            s.close()

    def _register_with_server(self, server_ip, tcp_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((server_ip, tcp_port))
                s.send("register".encode())
                response = s.recv(1024).decode()
                if response == "OK":
                    print(f"Successfully registered with server at {server_ip}")
                    self.is_registered = True  # Устанавливаем флаг успешной регистрации
        except Exception as e:
            print(f"Failed to register with server at {server_ip}: {e}")


######################################################################################################################


def run_discovery_client():
    client = DiscoveryClient()
    client.start()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ble args like port, kill process with port')
    parser.add_argument(
        '--kill_process_with_port',
        type=bool,
        default=True,
        help='provide a bool (default: True)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='provide an int port (default: 5000)'
    )
    args = parser.parse_args()

    # Kill process using the specified port if requested
    if args.kill_process_with_port:
        subprocess.run(f'fuser -s -TERM -k {args.port}/tcp', shell=True)

    # Start DiscoveryClient in a separate thread
    discovery_thread = threading.Thread(target=run_discovery_client)
    discovery_thread.daemon = True
    discovery_thread.start()

    # Start the Flask app
    app = create_app()
    app.run(host='0.0.0.0', port=args.port)