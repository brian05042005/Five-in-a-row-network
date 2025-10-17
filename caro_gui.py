# File: main_app.py
import tkinter as tk
import tkinter.messagebox as messagebox
import sys
import queue
from network import NetworkManager
from main import CaroGame

class ChessboardApp:
    PIXEL = 40
# File: caro_gui.py
import tkinter as tk
import tkinter.messagebox as messagebox
import sys
import queue
from network import NetworkManager
from main import CaroGame # <<< SỬA LỖI: Import từ file "main.py"

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
        self.remaining_time = 30
        self.username = ""
        self.game_started = False
        
        self.winning_line_coords = None

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
                    self.root.title(f"FiveinARow - Player: {self.username}")
                    self.setup_game_ui(click_handler=self.on_canvas_click)
                    self.status_bar.config(text="Waiting for an opponent...")

                elif command == "GAME_START":
                    opponent = parts[1]
                    self.my_piece_id = int(parts[2])
                    self.game_started = True
                    self.game.reset_board()
                    self.refresh_graphics()
                    piece_type = "O (Blue)" if self.my_piece_id == 1 else "X (Red)"
                    messagebox.showinfo("Game On!", f"Match started against {opponent}. You are {piece_type}")

                elif command == "YOUR_TURN":
                    self.my_turn = True
                    self.remaining_time = int(parts[1])
                    self.start_timer()

                elif command == "UPDATE_BOARD":
                    coords = parts[1].split(',')
                    col, row = int(coords[0]), int(coords[1])
                    piece_id = int(parts[2])

                    if self.game.board[row][col] == 0:
                        self.game.make_move(row, col, piece_id)
                        self.draw_piece(col, row, piece_id)

                    winner, line_coords = self.game.check_win_and_get_line(row, col)
                    if winner:
                        self.winning_line_coords = line_coords
                        self.draw_winning_line()
                        
                        if (winner == 'O won' and self.my_piece_id == 1) or \
                           (winner == 'X won' and self.my_piece_id == 2):
                            self.network.send_message("GAME_WIN")

                elif command == "GAME_WIN":
                    self.my_turn = False
                    self.stop_timer()
                    self.status_bar.config(text="You won!")
                    self.handle_game_result("You won")

                elif command == "GAME_LOSE":
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
            
    def handle_click_offline(self, event):
        if self.winning_line_coords:
            return

        col, row = self.get_index_from_position(event.x, event.y)

        if self.game.board[row][col] == 0:
            self.game.make_move(row, col, 1)
            self.draw_piece(col, row, 1)

            winner, line_coords = self.game.check_win_and_get_line(row, col)
            if winner:
                self.winning_line_coords = line_coords
                self.draw_winning_line()
                self.root.update()
                self.handle_game_result_offline(winner)
                return
            
            self.status_bar.config(text="Máy đang suy nghĩ...")
            self.root.update_idletasks()
            self.root.after(1000, self.execute_ai_turn)

    def execute_ai_turn(self):
        ai_row, ai_col = self.game.best_move(2)
        if self.game.board[ai_row][ai_col] == 0:
            self.game.make_move(ai_row, ai_col, 2)
            self.draw_piece(ai_col, ai_row, 2)
        
        winner, line_coords = self.game.check_win_and_get_line(ai_row, ai_col)
        if winner:
            self.winning_line_coords = line_coords
            self.draw_winning_line()
            self.root.update()
            self.handle_game_result_offline(winner)
        else:
            self.status_bar.config(text="Chế độ Offline: Tới lượt bạn.")

    def draw_chessboard(self):
        for i in range(25):
            for j in range(25):
                x1, y1 = i * self.PIXEL, j * self.PIXEL
                x2, y2 = x1 + self.PIXEL, y1 + self.PIXEL
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="black", width=1)
                
    def draw_piece(self, col, row, piece_id):
        x_center = col * self.PIXEL + self.PIXEL / 2
        y_center = row * self.PIXEL + self.PIXEL / 2
        radius = self.PIXEL / 2 - 5
        if piece_id == 1:
            self.canvas.create_oval(x_center - radius, y_center - radius, x_center + radius, y_center + radius, outline="blue", width=3)
        elif piece_id == 2:
            self.canvas.create_line(x_center - radius, y_center - radius, x_center + radius, y_center + radius, fill="red", width=3)
            self.canvas.create_line(x_center + radius, y_center - radius, x_center - radius, y_center + radius, fill="red", width=3)

    def draw_winning_line(self):
        if not self.winning_line_coords:
            return
        
        (start_y, start_x), (end_y, end_x) = self.winning_line_coords
        
        x1 = start_x * self.PIXEL + self.PIXEL / 2
        y1 = start_y * self.PIXEL + self.PIXEL / 2
        x2 = end_x * self.PIXEL + self.PIXEL / 2
        y2 = end_y * self.PIXEL + self.PIXEL / 2
        
        self.canvas.create_line(x1, y1, x2, y2, fill="green", width=5)

    def refresh_graphics(self):
        self.canvas.delete("all")
        self.draw_chessboard()
        self.winning_line_coords = None

    def get_index_from_position(self, x, y):
        return x // self.PIXEL, y // self.PIXEL

    def start_timer(self):
        self.stop_timer()
        self.update_timer()

    def update_timer(self):
        if self.my_turn and self.remaining_time > 0:
            self.status_bar.config(text=f"Your turn! You have {self.remaining_time} seconds.")
            self.remaining_time -= 1
            self.timer_id = self.root.after(1000, self.update_timer)
        elif self.my_turn and self.remaining_time <= 0:
            self.my_turn = False
            self.status_bar.config(text="Time's up!")

    def stop_timer(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
            
    def handle_game_result(self, result_text):
        messagebox.showinfo("Game Over", result_text)
        self.game_started = False
        self.status_bar.config(text="Game over. Waiting for a new challenge.")

    def handle_game_result_offline(self, winner):
        message = ""
        if winner == 'O won': message = "Chúc mừng, bạn đã thắng!"
        elif winner == 'X won': message = "Rất tiếc, máy đã thắng!"
        elif winner == 'Draw': message = "Trận đấu hòa!"
        
        self.root.after(500, lambda: self.show_play_again_dialog(message))

    def show_play_again_dialog(self, message):
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
    def __init__(self, root):
        self.root = root
        self.root.title("FiveinARow")
        self.root.geometry("1000x1000")

        self.game = CaroGame()

        # ... (networking and state variables)
        self.message_queue = queue.Queue()
        self.network = NetworkManager(self.message_queue)
        self.my_turn = False
        self.my_piece_id = 0
        self.timer_id = None
        self.remaining_time = 30
        self.username = ""
        self.game_started = False
        
        # <<< BIẾN MỚI: Lưu trữ tọa độ đường thắng
        self.winning_line_coords = None

        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_mode_selection_ui()

    # ... (Các hàm UI và Networking không đổi, từ create_mode_selection_ui đến connect_to_server)
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
                    self.root.title(f"FiveinARow - Player: {self.username}")
                    self.setup_game_ui(click_handler=self.on_canvas_click)
                    self.status_bar.config(text="Waiting for an opponent...")

                elif command == "GAME_START":
                    opponent = parts[1]
                    self.my_piece_id = int(parts[2])
                    self.game_started = True
                    self.game.reset_board()
                    self.refresh_graphics() # Refresh sẽ reset cả đường thắng cũ
                    piece_type = "O (Blue)" if self.my_piece_id == 1 else "X (Red)"
                    messagebox.showinfo("Game On!", f"Match started against {opponent}. You are {piece_type}")

                elif command == "YOUR_TURN":
                    self.my_turn = True
                    self.remaining_time = int(parts[1])
                    self.start_timer()

                elif command == "UPDATE_BOARD":
                    coords = parts[1].split(',')
                    col, row = int(coords[0]), int(coords[1])
                    piece_id = int(parts[2])

                    if self.game.board[row][col] == 0:
                        self.game.make_move(row, col, piece_id)
                        self.draw_piece(col, row, piece_id)

                    # <<< THAY ĐỔI: Gọi hàm kiểm tra thắng mới
                    winner, line_coords = self.game.check_win_and_get_line(row, col)
                    if winner:
                        self.winning_line_coords = line_coords
                        self.draw_winning_line() # Vẽ đường kẻ
                        
                        # Chỉ người thắng mới gửi tin nhắn GAME_WIN
                        if (winner == 'O won' and self.my_piece_id == 1) or \
                           (winner == 'X won' and self.my_piece_id == 2):
                            self.network.send_message("GAME_WIN")

                elif command == "GAME_WIN":
                    self.my_turn = False
                    self.stop_timer()
                    self.status_bar.config(text="You won!")
                    self.handle_game_result("You won")

                elif command == "GAME_LOSE":
                    self.my_turn = False
                    self.stop_timer()
                    self.status_bar.config(text="You lose!")
                    # Đối phương đã vẽ đường thắng, mình không cần vẽ lại
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
            
   # <<< THAY THẾ HÀM CŨ BẰNG HÀM NÀY

    # <<< THAY THẾ HÀM CŨ BẰNG HÀM NÀY

    def handle_click_offline(self, event):
        """Xử lý click cho chế độ offline (đánh với máy)."""
        if self.winning_line_coords:
            return

        col, row = self.get_index_from_position(event.x, event.y)

        if self.game.board[row][col] == 0:
            self.game.make_move(row, col, 1)
            self.draw_piece(col, row, 1)

            winner, line_coords = self.game.check_win_and_get_line(row, col)
            if winner:
                self.winning_line_coords = line_coords
                self.draw_winning_line()
                self.root.update() # <<< THAY ĐỔI: Dùng lệnh update() mạnh hơn
                self.handle_game_result_offline(winner)
                return
            
            self.status_bar.config(text="Máy đang suy nghĩ...")
            self.root.update_idletasks()
            self.root.after(1000, self.execute_ai_turn)

    # <<< THAY THẾ HÀM CŨ BẰNG HÀM NÀY

    # <<< THAY THẾ HÀM CŨ BẰNG HÀM NÀY

    def execute_ai_turn(self):
        """Hàm này chứa logic đi cờ của máy."""
        ai_row, ai_col = self.game.best_move(2)
        if self.game.board[ai_row][ai_col] == 0:
            self.game.make_move(ai_row, ai_col, 2)
            self.draw_piece(ai_col, ai_row, 2)
        
        winner, line_coords = self.game.check_win_and_get_line(ai_row, ai_col)
        if winner:
            self.winning_line_coords = line_coords
            self.draw_winning_line()
            self.root.update() # <<< THAY ĐỔI: Dùng lệnh update() mạnh hơn
            self.handle_game_result_offline(winner)
        else:
            self.status_bar.config(text="Chế độ Offline: Tới lượt bạn.")

    def draw_chessboard(self):
        for i in range(25):
            for j in range(25):
                x1, y1 = i * self.PIXEL, j * self.PIXEL
                x2, y2 = x1 + self.PIXEL, y1 + self.PIXEL
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="black", width=1)
                
    def draw_piece(self, col, row, piece_id):
        x_center = col * self.PIXEL + self.PIXEL / 2
        y_center = row * self.PIXEL + self.PIXEL / 2
        radius = self.PIXEL / 2 - 5
        if piece_id == 1:
            self.canvas.create_oval(x_center - radius, y_center - radius, x_center + radius, y_center + radius, outline="blue", width=3)
        elif piece_id == 2:
            self.canvas.create_line(x_center - radius, y_center - radius, x_center + radius, y_center + radius, fill="red", width=3)
            self.canvas.create_line(x_center + radius, y_center - radius, x_center - radius, y_center + radius, fill="red", width=3)

    # <<< HÀM MỚI: Vẽ đường kẻ chiến thắng
    def draw_winning_line(self):
        if not self.winning_line_coords:
            return
        
        (start_y, start_x), (end_y, end_x) = self.winning_line_coords
        
        # Chuyển tọa độ bàn cờ sang tọa độ pixel trên canvas
        x1 = start_x * self.PIXEL + self.PIXEL / 2
        y1 = start_y * self.PIXEL + self.PIXEL / 2
        x2 = end_x * self.PIXEL + self.PIXEL / 2
        y2 = end_y * self.PIXEL + self.PIXEL / 2
        
        # Vẽ một đường thẳng màu xanh lá, dày để nổi bật
        self.canvas.create_line(x1, y1, x2, y2, fill="green", width=5)

    def refresh_graphics(self):
        self.canvas.delete("all")
        self.draw_chessboard()
        # <<< THAY ĐỔI: Reset lại đường thắng khi bắt đầu ván mới
        self.winning_line_coords = None

    def get_index_from_position(self, x, y):
        return x // self.PIXEL, y // self.PIXEL

    # ... (Các hàm timer và xử lý kết quả game không đổi)
    def start_timer(self):
        self.stop_timer()
        self.update_timer()

    def update_timer(self):
        if self.my_turn and self.remaining_time > 0:
            self.status_bar.config(text=f"Your turn! You have {self.remaining_time} seconds.")
            self.remaining_time -= 1
            self.timer_id = self.root.after(1000, self.update_timer)
        elif self.my_turn and self.remaining_time <= 0:
            self.my_turn = False
            self.status_bar.config(text="Time's up!")

    def stop_timer(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
            
    def handle_game_result(self, result_text):
        messagebox.showinfo("Game Over", result_text)
        self.game_started = False
        self.status_bar.config(text="Game over. Waiting for a new challenge.")

    def handle_game_result_offline(self, winner):
        message = ""
        if winner == 'O won': message = "Chúc mừng, bạn đã thắng!"
        elif winner == 'X won': message = "Rất tiếc, máy đã thắng!"
        elif winner == 'Draw': message = "Trận đấu hòa!"
        
        # Đợi một chút trước khi hiện thông báo để người chơi thấy đường kẻ
        self.root.after(500, lambda: self.show_play_again_dialog(message))

    def show_play_again_dialog(self, message):
        """Hàm riêng để hiển thị dialog hỏi chơi lại."""
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