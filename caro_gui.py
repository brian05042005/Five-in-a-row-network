# File: main_app.py
import tkinter as tk
import tkinter.messagebox as messagebox
import sys
import queue
from network import NetworkManager
from main import CaroGame

class ChessboardApp:
    PIXEL = 40

    def __init__(self, root):
        self.root = root
        self.root.title("FiveinARow")
        self.root.geometry("1000x1000")

        self.game = CaroGame()

        self.message_queue = queue.Queue()
        self.network = NetworkManager(self.message_queue)
        self.my_turn = False
        self.my_piece_id = 0
        self.timer_id = None
        self.remaining_time = 50
        self.username = ""
        self.game_started = False

        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_mode_selection_ui()

    def create_mode_selection_ui(self):
        self.mode_selection_frame = tk.Frame(self.main_frame)
        self.mode_selection_frame.pack(pady=200)

        tk.Label(self.mode_selection_frame, text="CHỌN CHẾ ĐỘ CHƠI", font=("Arial", 24, "bold")).pack(pady=20)

        online_button = tk.Button(self.mode_selection_frame, text="Chơi Online", font=("Arial", 16),
                                   width=20, command=self.show_login_ui)
        online_button.pack(pady=10)

        offline_button = tk.Button(self.mode_selection_frame, text="Chơi Offline (Với Máy)", font=("Arial", 16),
                                    width=20, command=self.start_offline_game)
        offline_button.pack(pady=10)

    def show_login_ui(self):
        self.mode_selection_frame.destroy()
        self.create_login_ui()

    def start_offline_game(self):
        self.mode_selection_frame.destroy()
        # <<< THAY ĐỔI 3: Đặt tiêu đề cho chế độ offline
        self.root.title("FiveinARow - Offline Mode")
        self.setup_game_ui(click_handler=self.handle_click_offline) 
        self.status_bar.config(text="Chế độ Offline: Bạn đi trước (Quân O).")

    def create_login_ui(self):
        self.login_frame = tk.Frame(self.main_frame)
        self.login_frame.pack(pady=200)

        tk.Label(self.login_frame, text="Your Name:", font=("Arial", 14)).pack(pady=5)
        self.name_entry = tk.Entry(self.login_frame, font=("Arial", 14))
        self.name_entry.pack(pady=5)

        tk.Label(self.login_frame, text="Server IP:", font=("Arial", 14)).pack(pady=5)
        self.ip_entry = tk.Entry(self.login_frame, font=("Arial", 14))
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack(pady=5)

        connect_button = tk.Button(self.login_frame, text="Connect and Find Match", font=("Arial", 16),
                                   command=self.connect_to_server)
        connect_button.pack(pady=20)

    def connect_to_server(self):
        self.username = self.name_entry.get()
        ip = self.ip_entry.get()
        if not self.username or not ip:
            messagebox.showerror("Error", "Please enter your name and server IP.")
            return

        if self.network.connect(ip, 13000):
            self.network.send_message(f"LOGIN|{self.username}")
            self.root.after(100, self.process_messages)
        else:
            messagebox.showerror("Error", "Could not connect to the server.")

    def setup_game_ui(self, click_handler):
        if hasattr(self, 'login_frame'):
            self.login_frame.destroy()

        # <<< THAY ĐỔI 2: Thêm font lớn hơn và in nghiêng cho thanh trạng thái/thời gian
        font_style = ("Arial", 14, "italic")
        self.status_bar = tk.Label(self.main_frame, text="...", bd=1, relief=tk.SUNKEN, anchor=tk.W, font=font_style)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas = tk.Canvas(self.main_frame, width=1000, height=1000, bg="White")
        self.canvas.pack()
        self.draw_chessboard()
        
        self.canvas.bind("<Button-1>", click_handler)

    def process_messages(self):
        try:
            while not self.message_queue.empty():
                message = self.message_queue.get_nowait()
                parts = message.split('|')
                command = parts[0]

                if command == "LOGIN_SUCCESS":
                    messagebox.showinfo("Success", "Connected!")
                    # <<< THAY ĐỔI 3: Cập nhật tiêu đề cửa sổ với tên người chơi
                    self.root.title(f"FiveinARow - Player: {self.username}")
                    self.setup_game_ui(click_handler=self.on_canvas_click)
                    self.status_bar.config(text="Waiting for an opponent...")

                elif command == "GAME_START":
                    # ... (không thay đổi)
                    opponent = parts[1]
                    self.my_piece_id = int(parts[2])
                    self.game_started = True
                    self.game.reset_board()
                    self.refresh_graphics()
                    piece_type = "O (Blue)" if self.my_piece_id == 1 else "X (Red)"
                    messagebox.showinfo("Game On!", f"Match started against {opponent}. You are {piece_type}")

                elif command == "YOUR_TURN":
                    # ... (không thay đổi)
                    self.my_turn = True
                    self.remaining_time = int(parts[1])
                    self.start_timer()

                elif command == "UPDATE_BOARD":
                    # ... (không thay đổi)
                    coords = parts[1].split(',')
                    x, y = int(coords[0]), int(coords[1])
                    piece_id = int(parts[2])

                    if self.game.board[y][x] == 0:
                        self.game.make_move(y, x, piece_id)
                        self.draw_piece(x, y, piece_id)

                    winner = self.game.is_win()
                    if (winner == 'O won' and self.my_piece_id == 1) or \
                       (winner == 'X won' and self.my_piece_id == 2):
                        self.network.send_message("GAME_WIN")

                elif command == "GAME_WIN":
                    # ... (không thay đổi)
                    self.my_turn = False
                    self.stop_timer()
                    self.status_bar.config(text="You won!")
                    self.handle_game_result("You won")

                elif command == "GAME_LOSE":
                    # ... (không thay đổi)
                    self.my_turn = False
                    self.stop_timer()
                    self.status_bar.config(text="You lose!")
                    self.handle_game_result("You lose")

        finally:
            self.root.after(100, self.process_messages)

    def on_canvas_click(self, event):
        if not self.my_turn or not self.game_started:
            return

        col, row = self.get_index_from_position(event.x, event.y)

        if self.game.board[row][col] == 0:
            self.network.send_message(f"MOVE|{col},{row}")
            self.my_turn = False
            self.stop_timer()
            self.status_bar.config(text="Waiting for opponent's move...")
            
    # <<< THAY ĐỔI 1: Tách logic của máy ra để tạo độ trễ
    def handle_click_offline(self, event):
        """Xử lý click cho chế độ offline (chỉ xử lý lượt của người chơi)."""
        col, row = self.get_index_from_position(event.x, event.y)

        # Lượt người chơi
        if self.game.board[row][col] == 0:
            self.game.make_move(row, col, 1) # Người chơi là quân O
            self.draw_piece(col, row, 1)

            winner = self.game.is_win()
            if winner != 'continue playing':
                self.handle_game_result_offline(winner)
                return
            
            # Cập nhật giao diện và đợi 1 giây trước khi máy đi
            self.status_bar.config(text="Máy đang suy nghĩ...")
            self.root.update_idletasks() # Buộc giao diện cập nhật ngay lập tức
            self.root.after(1000, self.execute_ai_turn) # Gọi lượt của AI sau 1000ms

    # <<< HÀM MỚI: Thực thi lượt đi của AI
    def execute_ai_turn(self):
        """Hàm này chứa logic đi cờ của máy."""
        # Máy đi quân 2 (X)
        ai_row, ai_col = self.game.best_move(2)
        if self.game.board[ai_row][ai_col] == 0:
            self.game.make_move(ai_row, ai_col, 2)
            self.draw_piece(ai_col, ai_row, 2)
        
        winner = self.game.is_win()
        if winner != 'continue playing':
            self.handle_game_result_offline(winner)
        else:
            self.status_bar.config(text="Chế độ Offline: Tới lượt bạn.")

    def draw_chessboard(self):
        # ... (không thay đổi)
        for i in range(25):
            for j in range(25):
                x1, y1 = i * self.PIXEL, j * self.PIXEL
                x2, y2 = x1 + self.PIXEL, y1 + self.PIXEL
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="black", width=1)
                
    def draw_piece(self, col, row, piece_id):
        # ... (không thay đổi)
        x_center = col * self.PIXEL + self.PIXEL / 2
        y_center = row * self.PIXEL + self.PIXEL / 2
        radius = self.PIXEL / 2 - 5

        if piece_id == 1: # Quân O
            self.canvas.create_oval(x_center - radius, y_center - radius, x_center + radius, y_center + radius, outline="blue", width=3)
        elif piece_id == 2: # Quân X
            self.canvas.create_line(x_center - radius, y_center - radius, x_center + radius, y_center + radius, fill="red", width=3)
            self.canvas.create_line(x_center + radius, y_center - radius, x_center - radius, y_center + radius, fill="red", width=3)

    def refresh_graphics(self):
        # ... (không thay đổi)
        self.canvas.delete("all")
        self.draw_chessboard()

    def get_index_from_position(self, x, y):
        # ... (không thay đổi)
        return x // self.PIXEL, y // self.PIXEL

    def start_timer(self):
        # ... (không thay đổi)
        self.stop_timer()
        self.update_timer()

    def update_timer(self):
        # ... (không thay đổi)
        if self.my_turn and self.remaining_time > 0:
            self.status_bar.config(text=f"Your turn! You have {self.remaining_time} seconds.")
            self.remaining_time -= 1
            self.timer_id = self.root.after(1000, self.update_timer)
        elif self.my_turn and self.remaining_time <= 0:
            self.my_turn = False
            self.status_bar.config(text="Time's up!")

    def stop_timer(self):
        # ... (không thay đổi)
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
            
    def handle_game_result(self, result_text):
        # ... (không thay đổi)
        messagebox.showinfo("Game Over", result_text)
        self.game_started = False
        self.status_bar.config(text="Game over. Waiting for a new challenge.")

    def handle_game_result_offline(self, winner):
        # ... (không thay đổi)
        message = ""
        if winner == 'O won': message = "Chúc mừng, bạn đã thắng!"
        elif winner == 'X won': message = "Rất tiếc, máy đã thắng!"
        elif winner == 'Draw': message = "Trận đấu hòa!"
        
        messagebox.showinfo("Game Over", message)
        if messagebox.askyesno("Play Again?", "Bạn có muốn chơi lại không?"):
            self.game.reset_board()
            self.refresh_graphics()
            self.status_bar.config(text="Chế độ Offline: Bạn đi trước (Quân O).")
        else:
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChessboardApp(root)
    root.mainloop()