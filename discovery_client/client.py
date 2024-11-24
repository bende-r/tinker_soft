import socket
import threading
import json

class DiscoveryClient:
    def __init__(self, discovery_port=5000 ):
        self.discovery_port = discovery_port

    def start(self):
        udp_thread = threading.Thread(target=self._listen_for_discovery)
        udp_thread.daemon = True
        udp_thread.start()
        udp_thread.join()  # Keep the thread running indefinitely

    def _listen_for_discovery(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', self.discovery_port))

        try:
            while True:
                data, addr = s.recvfrom(1024)
                try:
                    message = json.loads(data.decode('utf-8'))
                    if message["type"] == "discovery":
                        self._register_with_server(addr[0], message["tcp_port"])
                except:
                    continue
        finally:
            s.close()

    def _register_with_server(self, server_ip, tcp_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((server_ip, tcp_port))
                s.send("register".encode())
                response = s.recv(1024).decode()
                if response == "OK":
                    print("Successfully registered with server at {}".format(server_ip))
        except:
            print("Failed to register with server at {}".format(server_ip))

if __name__ == "__main__":
    client = DiscoveryClient()
    client.start()