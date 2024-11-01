import socket
import threading
import json
from datetime import datetime

class DiscoveryClient:
    def __init__(self, discovery_port=5000):
        self.discovery_port = discovery_port
        
    def start(self):
        # Запускаем прослушивание broadcast сообщений
        udp_thread = threading.Thread(target=self._listen_for_discovery)
        udp_thread.daemon = True
        udp_thread.start()
    
    def _listen_for_discovery(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('', self.discovery_port))
            
            while True:
                data, addr = s.recvfrom(1024)
                try:
                    message = json.loads(data.decode())
                    if message["type"] == "discovery":
                        # Подключаемся к TCP серверу для регистрации
                        self._register_with_server(addr[0], message["tcp_port"])
                except:
                    continue
    
    def _register_with_server(self, server_ip, tcp_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((server_ip, tcp_port))
                s.send("register".encode())
                response = s.recv(1024).decode()
                if response == "OK":
                    print(f"Successfully registered with server at {server_ip}")
        except:
            print(f"Failed to register with server at {server_ip}")