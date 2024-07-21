import socket
import threading
import requests
import json
from django.core.cache import cache


def get_local_ip():
    try:
        # Use an external address to determine the correct IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))  # This is a public DNS server, it doesn't have to be reachable
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except Exception as e:
        print(f"Error: {e}")
        return None


class ServerSocket:
    def __init__(self, host='192.168.60.47', port=12344):
        self.host = get_local_ip()
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))

    def listen_for_connections(self):
        self.sock.listen(5)
        print(f"Listening on {self.host}:{self.port}")
        while True:
            conn, addr = self.sock.accept()
            print(f"Connected by {addr}")
            self.handle_connection(conn)

    def handle_connection(self, conn):
        with conn:
            while True:
                data = conn.recv(1024)
                print(data)
                if not data:
                    break
                self.process_data(data.decode('utf-8'))

    def process_data(self, data):
        self.store_message(data)
        # Extract latitude, longitude, and altitude from the string
        try:
            parts = data.strip().split(", ")
            lat = float(parts[0].split(": ")[1])
            lon = float(parts[1].split(": ")[1])
            alt = float(parts[2].split(": ")[1])
            print(f"Lat: {lat}, Lon: {lon}, Alt: {alt}")

            # Update the location in the Django cache
            self.update_drone_location(lat, lon, alt)
            # Store the message in the Django cache
        except (IndexError, ValueError) as e:
            print(f"Error processing data: {e}")

    def update_drone_location(self, lat, lon, alt):
        cache.set('drone_location', (lat, lon,alt))

    def store_message(self, message):
        # Retrieve current messages from cache, default to an empty list if none
        messages = cache.get('drone_messages', [])
        # Add the new message
        messages.append(message)
        # Store the updated list back in the cache
        cache.set('drone_messages', messages)


# Run the server socket in a separate thread
def run_server():
    server = ServerSocket(host=socket.gethostbyname(socket.gethostname()))
    server.listen_for_connections()


# Start the server in a background thread
server_thread = threading.Thread(target=run_server)
server_thread.daemon = True  # Allows the server to be stopped when Django stops
server_thread.start()
