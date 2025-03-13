import socket
import threading
from collections import deque


class UDPConnectionManager:
    def __init__(self, buffer_size=1024, max_deque_len=2):
        """
        Initializes the UDP connection manager.

        :param buffer_size: Buffer size for receiving data.
        """
        self.sock = None
        self.host = None
        self.port = None
        self.buffer_size = buffer_size
        self.running = False
        self.listen_thread = None
        self.data_queue = deque(maxlen=max_deque_len)
        self.lock = threading.Lock()  # Ensure thread-safe access to the deque

    def connect(self, host, port):
        """
        Establishes a UDP connection to the specified host and port.

        :param host: IP address or hostname of the ESP server.
        :param port: Port number.
        """
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # In UDP, connect() assigns a default address for sending and receiving.
        self.sock.connect((host, port))
        # Set a timeout to avoid blocking indefinitely.
        self.sock.settimeout(0.5)

    def listen(self):
        """
        Starts a background thread that listens for incoming data from the ESP
        and stores it in a deque.
        """
        if not self.sock:
            raise ValueError("Socket is not connected. Call connect() first.")
        self.running = True
        self.listen_thread = threading.Thread(target=self._listen_thread, daemon=True)
        self.listen_thread.start()

    def _listen_thread(self):
        """
        Internal function running in a thread that continuously listens for incoming data.
        """
        while self.running:
            try:
                data, addr = self.sock.recvfrom(self.buffer_size)
                if data:
                    with self.lock:
                        self.data_queue.append(data)
            except socket.timeout:
                continue  # Continue waiting without blocking the thread
            except Exception as e:
                print(f"Exception in listening thread: {e}")
                break

    def get_data(self):
        """
        Extracts all stored data from the deque.

        :return: List of received data.
        """
        with self.lock:
            data = list(self.data_queue)
            self.data_queue.clear()
        return data

    def send_data(self, data, address=None):
        """
        Sends data to the specified address. If address is None, sends data to the default host and port.

        :param data: Data to send (must be bytes).
        :param address: Optional tuple (host, port) specifying the destination.
        """
        if self.sock is None:
            raise ValueError("Socket is not connected. Call connect() first.")
        if address:
            self.sock.sendto(data, address)
        else:
            self.sock.send(data)

    def close(self):
        """
        Closes the connection and stops the listening thread.
        """
        self.running = False
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join()
        if self.sock:
            self.sock.close()
            self.sock = None


# Example usage:
if __name__ == "__main__":
    udp_manager = UDPConnectionManager()
    udp_manager.connect("192.168.1.100", 12345)
    udp_manager.listen()

    import time

    try:
        while True:
            time.sleep(1)
            # In the RL environment's step method, you can call get_data() to retrieve the data.
            received_data = udp_manager.get_data()
            if received_data:
                print("Received data:", received_data)
            # Example of sending data to the default host and port:
            udp_manager.send_data(b"Hello ESP")
            # Or send data to a specific address:
            # udp_manager.send_data(b"Hello Device", ("192.168.1.101", 12345))
    except KeyboardInterrupt:
        udp_manager.close()
