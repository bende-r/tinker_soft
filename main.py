# main.py
import subprocess
import argparse
import signal
import sys
from flask_server.flask_server import create_app
from discovery_client.client import DiscoveryClient

def signal_handler(signum, frame):
    print("\nSignal received, shutting down...")
    sys.exit(0)

def start_discovery_client(discovery_port):
    client = DiscoveryClient(discovery_port=discovery_port)
    if client.start():
        return client
    return None

def create_parser():
    parser = argparse.ArgumentParser(description='Flask server with network discovery')
    parser.add_argument(
        '--kill_process_with_port',
        type=bool,
        default=True,
        help='provide an bool (default: True)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Flask server port (default: 5000)'
    )
    parser.add_argument(
        '--discovery_port',
        type=int,
        default=5001,
        help='Discovery service port (default: 5001)'
    )
    return parser

def main():
    # Регистрируем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    parser = create_parser()
    args = parser.parse_args()
    discovery_client = None

    try:
        # Убиваем процесс, если нужно
        if args.kill_process_with_port:
            subprocess.run(f'fuser -s -TERM -k {args.port}/tcp', shell=True)

        # Запускаем клиент обнаружения
        discovery_client = start_discovery_client(args.discovery_port)
        if not discovery_client:
            print("Failed to start discovery client")
            sys.exit(1)

        # Создаем и запускаем Flask приложение
        app = create_app()
        app.discovery_client = discovery_client
        app.run(host='0.0.0.0', port=args.port)

    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, shutting down...")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Корректно останавливаем клиент обнаружения
        if discovery_client and discovery_client.is_running():
            discovery_client.stop()

if __name__ == '__main__':
    main()


# import subprocess
# import argparse
# import socket
# import json
# import threading

# from flask_server.flask_server import create_app
# from logger.logger import get_logger

# logger = get_logger(__name__)

# def get_own_ip():
#     try:
#         # Create a socket connection to an external host (Google's DNS here) to determine the IP
#         # Note: No actual data is sent; it's just to get the local network's IP
#         with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
#             s.connect(("8.8.8.8", 80))  # Google DNS, just for IP discovery
#             ip_address = s.getsockname()[0]
#         return ip_address
#     except Exception as e:
#         logger.error(f"Could not determine IP address: {e}")
#         return None

# def listen_for_discovery():
#     """ Listens for broadcast discovery requests and responds with device information. """
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     sock.bind(("", 5002))  # Listen on port 5002 for discovery messages

#     logger.info("Listening for discovery requests...")

#     while True:
#         try:
#             # Receive the broadcast message
#             data, address = sock.recvfrom(1024)
#             message = data.decode()
#             logger.info(f"Received discovery message from {address}: {message}")

#             # Respond if the message matches "DISCOVER_DEVICES"
#             if message == "DISCOVER_DEVICES":
#                 response = json.dumps(get_own_ip()).encode()
#                 sock.sendto(response, address)  # Send device info back to the sender
#                 logger.info(f"Sent device info to {address}")

#         except Exception as e:
#             logger.error(f"Error while responding to discovery: {e}")

# # Command-line argument parsing
# parser = argparse.ArgumentParser(description='BLE arguments for port management')
# parser.add_argument(
#     '--kill_process_with_port',
#     type=bool,
#     default=True,
#     help='Terminate any process using the specified port before starting (default: True)'
# )
# parser.add_argument(
#     '--port',
#     type=int,
#     default=5000,
#     help='Port for the Flask server (default: 5000)'
# )

# if __name__ == '__main__':
#     args = parser.parse_args()

#     # Kill any process using the specified port if required
#     if args.kill_process_with_port:
#         subprocess.run(f'fuser -s -TERM -k {args.port}/tcp', shell=True)

#     # Start the device discovery listener in a separate thread
#     discovery_thread = threading.Thread(target=listen_for_discovery, daemon=True)
#     discovery_thread.start()

#     # Start the Flask application
#     app = create_app()
#     app.run(host='0.0.0.0', port=args.port)



# import subprocess
# import argparse
# import threading
# import socket
# import json

# from flask_server.flask_server import create_app

# # Function to get the IP address of the device
# def get_device_ip():
#     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     try:
#         s.connect(("8.8.8.8", 80))
#         ip = s.getsockname()[0]
#     finally:
#         s.close()
#     return ip

# # Function to listen for broadcast discovery messages and respond with IP
# def listen_for_broadcast():
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
#     sock.bind(("", 5002))  # Listening on port 5002 for broadcast messages

#     print("Listening for discovery requests...")

#     while True:
#         data, address = sock.recvfrom(1024)
#         if data.decode() == "DISCOVER_DEVICES":
#             response = json.dumps({"ip": get_device_ip()})
#             sock.sendto(response.encode(), address)
#             print(f"Responded to discovery request from {address[0]} with IP {response}")

# # Command-line argument parsing
# parser = argparse.ArgumentParser(description='ble args like port, kill process with port')
# parser.add_argument(
#     '--kill_process_with_port',
#     type=bool,
#     default=True,
#     help='provide a bool (default: True)'
# )
# parser.add_argument(
#     '--port',
#     type=int,
#     default=5000,
#     help='provide an int port (default: 5000)'
# )

# if __name__ == '__main__':
#     args = parser.parse_args()
    
#     # Kill process running on specified port if enabled
#     if args.kill_process_with_port:
#         subprocess.run(f'fuser -s -TERM -k {args.port}/tcp', shell=True)
    
#     # Start broadcast listener in a separate thread
#     broadcast_thread = threading.Thread(target=listen_for_broadcast, daemon=True)
#     broadcast_thread.start()
    
#     # Start the Flask server
#     app = create_app()
#     app.run(host='0.0.0.0', port=args.port)








# import subprocess
# import argparse

# from flask_server.flask_server import create_app

# parser = argparse.ArgumentParser(description='ble args like port, kill process with port')
# parser.add_argument(
#     '--kill_process_with_port',
#     type=bool,
#     default=True,
#     help='provide an bool (default: True)'
# )
# parser.add_argument(
#     '--port',
#     type=int,
#     default=5000,
#     help='provide an int port (default: 5000)'
# )
# if __name__ == '__main__':
#     args = parser.parse_args()
#     if args.kill_process_with_port:
#         subprocess.run(f'fuser -s -TERM -k {args.port}/tcp', shell=True)
#     app = create_app()
#     app.run(host='0.0.0.0', port=args.port)