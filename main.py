import subprocess
import argparse

from flask_server.flask_server import create_app

parser = argparse.ArgumentParser(description='ble args like port, kill process with port')
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
    help='provide an int port (default: 5000)'
)
if __name__ == '__main__':
    args = parser.parse_args()
    if args.kill_process_with_port:
        subprocess.run(f'fuser -s -TERM -k {args.port}/tcp', shell=True)
    app = create_app()
    app.run(host='0.0.0.0', port=args.port)

