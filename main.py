import subprocess
import argparse
import threading
from flask_server.flask_server import create_app
import socket
import json

class DiscoveryClient:
    def __init__(self, discovery_port=5000):
        self.discovery_port = discovery_port

    def start(self):
        udp_thread = threading.Thread(target=self._listen_for_discovery)
        udp_thread.daemon = True
        udp_thread.start()

    def _listen_for_discovery(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', self.discovery_port))

        try:
            while True:
                data, addr = s.recvfrom(1024)
                try:
                    message = json.loads(data.decode('utf-8'))
                    #print(f"got message {message}")
                    if message["type"] == "discovery":
                        self._register_with_server(addr[0], message["tcp_port"])
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
        except Exception as e:
            print(f"Failed to register with server at {server_ip}: {e}")


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