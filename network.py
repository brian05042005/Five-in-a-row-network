import socket
import threading
import queue

class NetworkManager:
    def __init__(self, message_queue):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.message_queue = message_queue # Dùng queue để giao tiếp an toàn giữa các thread

    def connect(self, host, port):
        try:
            self.client.connect((host, port))
            # Bắt đầu một thread để lắng nghe tin nhắn từ server
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True # Thread sẽ tự tắt khi chương trình chính kết thúc
            receive_thread.start()
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def send_message(self, message):
        try:
            self.client.sendall(message.encode('utf-8'))
        except Exception as e:
            print(f"Error sending message: {e}")

    def receive_messages(self):
        while True:
            try:
                data = self.client.recv(1024).decode('utf-8')
                if data:
                    # Đưa tin nhắn vào queue để thread chính xử lý
                    self.message_queue.put(data)
            except Exception as e:
                print(f"Lost connection to server: {e}")
                self.message_queue.put("CONNECTION_LOST")
                break