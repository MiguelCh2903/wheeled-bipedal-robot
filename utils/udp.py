import socket
import threading
import logging
from collections import deque
from typing import Optional, Tuple, List

# Configure logging for professional output
logger = logging.getLogger(__name__)


class UDPConnectionManager:
    """
    Manages a UDP connection with non-blocking listening on a separate thread.
    """

    def __init__(self, buffer_size: int = 1024, max_deque_len: int = 2) -> None:
        """
        Initializes the UDP connection manager.

        :param buffer_size: The size of the buffer used for receiving data.
        :param max_deque_len: Maximum number of data entries stored in the deque.
        """
        self.sock: Optional[socket.socket] = None
        self.host: Optional[str] = None
        self.port: Optional[int] = None
        self.buffer_size = buffer_size
        self.running = False
        self.listen_thread: Optional[threading.Thread] = None
        # The deque now stores tuples (data, address) to also keep track of sender.
        self.data_queue: deque = deque(maxlen=max_deque_len)
        self.lock = threading.Lock()

    def bind(self, host: str, port: int) -> None:
        """
        Binds the UDP socket to the specified host and port.

        :param host: IP address or hostname to bind.
        :param port: Port number.
        """
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.sock.bind((host, port))
            # Set a timeout to avoid indefinite blocking.
            self.sock.settimeout(0.5)
            logger.info(f"Socket successfully bound to {host}:{port}")
        except socket.error as e:
            logger.exception("Failed to bind the socket.")
            raise e

    def listen(self) -> None:
        """
        Starts a background thread that listens for incoming data.
        """
        if not self.sock:
            raise ValueError("Socket is not bound. Call bind() first.")
        self.running = True
        self.listen_thread = threading.Thread(target=self._listen_thread, daemon=True)
        self.listen_thread.start()
        logger.info("Started listening thread.")

    def _listen_thread(self) -> None:
        """
        Internal function that continuously listens for incoming data.
        """
        while self.running:
            try:
                data, addr = self.sock.recvfrom(self.buffer_size)
                if data:
                    with self.lock:
                        self.data_queue.append((data, addr))
                    logger.debug(f"Received data from {addr}: {data}")
            except socket.timeout:
                continue  # Expected timeout; continue listening.
            except Exception as e:
                logger.exception(f"Exception in listening thread: {e}")
                break

    def get_data(self) -> List[Tuple[bytes, Tuple[str, int]]]:
        """
        Retrieves and clears all stored data from the queue.

        :return: A list of tuples containing received data and sender's address.
        """
        with self.lock:
            data_list = list(self.data_queue)
            self.data_queue.clear()
        return data_list

    def send_data(self, data: bytes, address: Optional[Tuple[str, int]] = None) -> None:
        """
        Sends data via UDP.

        :param data: Data to send (must be bytes).
        :param address: Optional tuple (host, port) specifying the destination.
                        If not provided, sends to the default bound address.
        """
        if self.sock is None:
            raise ValueError("Socket is not bound. Call bind() first.")
        try:
            if address:
                sent_bytes = self.sock.sendto(data, address)
                logger.debug(f"Sent {sent_bytes} bytes to {address}")
            else:
                if self.host is None or self.port is None:
                    raise ValueError("Default address is not set.")
                sent_bytes = self.sock.sendto(data, (self.host, self.port))
                logger.debug(f"Sent {sent_bytes} bytes to default address {(self.host, self.port)}")
        except Exception as e:
            logger.exception("Failed to send data.")
            raise e

    def close(self) -> None:
        """
        Closes the UDP connection and stops the listening thread.
        """
        self.running = False
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=1)
            logger.info("Listening thread terminated.")
        if self.sock:
            self.sock.close()
            logger.info("Socket closed.")
            self.sock = None

    def __enter__(self):
        """
        Enables use of UDPConnectionManager in a context manager (with statement).
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Ensures proper resource cleanup when exiting the context.
        """
        self.close()


# Example usage:
if __name__ == "__main__":
    from config import *

    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    udp_manager = UDPConnectionManager()
    udp_manager.bind(HOST, PORT)
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
            udp_manager.send_data(b"Hello ESP", ("192.168.1.45", 8888))
            # Or send data to a specific address:
            # udp_manager.send_data(b"Hello Device", ("192.168.1.101", 12345))
    except KeyboardInterrupt:
        udp_manager.close()
