# discovery_client.py
import socket
import threading
import json
import time
from logger.logger import get_logger

logger = get_logger(__name__)

class DiscoveryClient:
    def __init__(self, discovery_port=5001):
        self.discovery_port = discovery_port
        self._running = False
        self._stop_event = threading.Event()
        self.server_info = None
        self.udp_thread = None
        
    def start(self):
        if not self._running:
            try:
                self._running = True
                self._stop_event.clear()
                # Запускаем прослушивание broadcast сообщений
                self.udp_thread = threading.Thread(target=self._listen_for_discovery)
                self.udp_thread.daemon = True
                self.udp_thread.start()
                logger.info("Discovery client started")
                return True
            except Exception as e:
                logger.error(f"Failed to start discovery client: {e}")
                self._running = False
                return False
        return False
    
    def stop(self):
        """Останавливает клиент обнаружения"""
        if self._running:
            logger.info("Stopping discovery client...")
            self._running = False
            self._stop_event.set()
            if self.udp_thread and self.udp_thread.is_alive():
                self.udp_thread.join(timeout=2)  # Ждем завершения потока максимум 2 секунды
            logger.info("Discovery client stopped")
    
    def is_running(self):
        """Возвращает текущее состояние клиента"""
        return self._running
        
    def get_server_info(self):
        """Возвращает информацию о последнем найденном сервере"""
        return self.server_info
    
    def _listen_for_discovery(self):
        """Прослушивает broadcast сообщения от сервера"""
        while not self._stop_event.is_set():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind(('', self.discovery_port))
                    s.settimeout(1)  # Таймаут для проверки события остановки
                    
                    while not self._stop_event.is_set():
                        try:
                            data, addr = s.recvfrom(1024)
                            if self._stop_event.is_set():
                                break
                            
                            try:
                                message = json.loads(data.decode())
                                if message["type"] == "discovery":
                                    self.server_info = {
                                        "server_ip": addr[0],
                                        "tcp_port": message["tcp_port"]
                                    }
                                    self._register_with_server(addr[0], message["tcp_port"])
                            except json.JSONDecodeError:
                                continue
                        except socket.timeout:
                            continue
                        
            except Exception as e:
                if not self._stop_event.is_set():
                    logger.error(f"UDP listening error: {e}")
                    time.sleep(1)
    
    def _register_with_server(self, server_ip, tcp_port):
        """Регистрирует клиента на сервере"""
        if self._stop_event.is_set():
            return
            
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((server_ip, tcp_port))
                s.send("register".encode())
                response = s.recv(1024).decode()
                if response == "OK":
                    logger.info(f"Successfully registered with server at {server_ip}")
        except Exception as e:
            logger.error(f"Failed to register with server at {server_ip}: {e}")