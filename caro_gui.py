import tkinter as tk
from tkinter import ttk, messagebox
import queue
from network import NetworkManager
from main import CaroGame
from modern_game_ui import GameBoardUI # <<< Import giao diện mới

class ChessboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Five in a Row")
        self.root.configure(bg="#F0F0F0") # Màu nền cho cửa sổ

        # Sử dụng theme 'clam' để có giao diện hiện đại hơn
        style = ttk.Style()
        style.theme_use('clam')

        # Khởi tạo logic game và mạng
        self.game = CaroGame()
        self.network = NetworkManager(queue.Queue())
        self.message_queue = self.network.message_queue

        # Trạng thái game
        self.my_turn = False
        self.my_piece_id = 0
        self.username = ""
        self.game_started = False
        self.timer_id = None
        
        # Frame chính
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_mode_selection_ui()

    def create_mode_selection_ui(self):
        self.clear_main_frame()
        self.mode_selection_frame = ttk.Frame(self.main_frame)
        self.mode_selection_frame.pack(expand=True)

        ttk.Label(self.mode_selection_frame, text="CHỌN CHẾ ĐỘ CHƠI", font=("Arial", 24, "bold")).pack(pady=20)
        ttk.Button(self.mode_selection_frame, text="Chơi Online", style='Accent.TButton', command=self.show_login_ui).pack(pady=10, ipady=5, ipadx=10)
        ttk.Button(self.mode_selection_frame, text="Chơi Offline (Với Máy)", command=self.start_offline_game).pack(pady=10, ipady=5, ipadx=10)
        
        # Cấu hình style cho nút nhấn
        s = ttk.Style()
        s.configure('Accent.TButton', font=('Arial', 14), background='#3498DB', foreground='white')
        s.map('Accent.TButton', background=[('active', '#2980B9')])

    def show_login_ui(self):
        self.clear_main_frame()
        self.login_frame = ttk.Frame(self.main_frame)
        self.login_frame.pack(expand=True)

        ttk.Label(self.login_frame, text="KẾT NỐI SERVER", font=("Arial", 18, "bold")).pack(pady=10)

        ttk.Label(self.login_frame, text="Tên người chơi:", font=("Arial", 12)).pack(pady=(10,0))
        self.name_entry = ttk.Entry(self.login_frame, font=("Arial", 12), width=30)
        self.name_entry.pack(pady=5, padx=20)

        ttk.Label(self.login_frame, text="Địa chỉ IP của Server:", font=("Arial", 12)).pack(pady=(10,0))
        self.ip_entry = ttk.Entry(self.login_frame, font=("Arial", 12), width=30)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack(pady=5, padx=20)
        
        ttk.Label(self.login_frame, text="(Nhập IP của máy chạy server nếu chơi qua mạng LAN)", font=("Arial", 9, "italic")).pack()
        ttk.Button(self.login_frame, text="Tìm trận", style='Accent.TButton', command=self.connect_to_server).pack(pady=20, ipady=5, ipadx=10)

    def start_offline_game(self):
        self.root.title("Five in a Row - Chơi với máy")
        self.setup_game_view()
        self.status_bar.config(text="Chế độ Offline: Bạn đi trước (Quân Đen).")

    def connect_to_server(self):
        self.username = self.name_entry.get().strip()
        ip = self.ip_entry.get().strip()
        if not self.username or not ip:
            messagebox.showerror("Lỗi", "Vui lòng nhập tên và địa chỉ IP.")
            return
        
        if self.network.connect(ip, 13000):
            self.network.send_message(f"LOGIN|{self.username}")
            self.root.after(100, self.process_messages)
            self.show_waiting_screen()
        else:
            messagebox.showerror("Lỗi kết nối", f"Không thể kết nối đến server tại {ip}:13000.")

    def show_waiting_screen(self):
        self.clear_main_frame()
        self.waiting_frame = ttk.Frame(self.main_frame)
        self.waiting_frame.pack(expand=True)
        ttk.Label(self.waiting_frame, text="Đang tìm đối thủ...", font=("Arial", 18)).pack()
        progress = ttk.Progressbar(self.waiting_frame, mode='indeterminate')
        progress.pack(pady=20, padx=50, fill=tk.X)
        progress.start()

    def setup_game_view(self):
        self.clear_main_frame()
        
        # Frame chứa thông tin và bàn cờ
        game_container = ttk.Frame(self.main_frame)
        game_container.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Thanh trạng thái ở trên
        self.status_bar = ttk.Label(game_container, text="...", font=("Arial", 14, "italic"), anchor=tk.CENTER)
        self.status_bar.pack(pady=(0, 10), fill=tk.X)
        
        # Tích hợp giao diện bàn cờ mới
        self.game_board = GameBoardUI(game_container, size=25, cell_size=28)
        self.game_board.move_callback = self.on_board_click

    def on_board_click(self, row, col):
        """Callback được gọi từ GameBoardUI khi người chơi click."""
        if self.game.board[row][col] != 0: # Ô đã được đánh
            return
        
        # Phân luồng xử lý cho online hoặc offline
        if self.game_started: # Chế độ Online
            if self.my_turn:
                self.network.send_message(f"MOVE|{col},{row}")
                self.my_turn = False
                self.stop_timer()
                self.status_bar.config(text="Đang chờ đối thủ...")
        else: # Chế độ Offline
             if not self.game_board.winning_line:
                self.handle_click_offline(row, col)

    def handle_click_offline(self, row, col):
        """Xử lý logic cho một lượt đi trong chế độ offline."""
        # Lượt người chơi
        self.game.make_move(row, col, 1)
        self.game_board.place_piece(row, col, 1)

        winner, line_coords = self.game.check_win_and_get_line(row, col)
        if winner:
            self.game_board.draw_winning_line(line_coords[0], line_coords[1])
            self.root.update()
            self.handle_game_result_offline(winner)
            return
        
        # Chuẩn bị cho lượt của máy
        self.status_bar.config(text="Máy đang suy nghĩ...")
        self.root.update_idletasks()
        self.root.after(500, self.execute_ai_turn) # Độ trễ ngắn hơn

    def execute_ai_turn(self):
        ai_row, ai_col = self.game.best_move(self.game.board, 2)
        if self.game.board[ai_row][ai_col] == 0:
            self.game.make_move(ai_row, ai_col, 2)
            self.game_board.place_piece(ai_row, ai_col, 2)
        
        winner, line_coords = self.game.check_win_and_get_line(ai_row, ai_col)
        if winner:
            self.game_board.draw_winning_line(line_coords[0], line_coords[1])
            self.root.update()
            self.handle_game_result_offline(winner)
        else:
            self.status_bar.config(text="Chế độ Offline: Tới lượt bạn.")

    def process_messages(self):
        try:
            while not self.message_queue.empty():
                message = self.message_queue.get_nowait()
                parts = message.split('|')
                command = parts[0]

                if command == "GAME_START":
                    self.setup_game_view()
                    opponent = parts[1]
                    self.my_piece_id = int(parts[2])
                    self.game_started = True
                    self.root.title(f"{self.username} vs {opponent}")
                    piece_type = "Đen (Đi trước)" if self.my_piece_id == 1 else "Trắng"
                    messagebox.showinfo("Bắt đầu!", f"Trận đấu bắt đầu!\nBạn là quân {piece_type}.")

                elif command == "YOUR_TURN":
                    self.my_turn = True
                    self.start_timer(int(parts[1]))

                elif command == "UPDATE_BOARD":
                    col, row, piece_id = map(int, parts[1].split(','))
                    if self.game.board[row][col] == 0:
                        self.game.make_move(row, col, piece_id)
                        self.game_board.place_piece(row, col, piece_id)

                    winner, line_coords = self.game.check_win_and_get_line(row, col)
                    if winner:
                        self.game_board.draw_winning_line(line_coords[0], line_coords[1])
                        # Server sẽ gửi thông báo thắng/thua riêng
                        
                elif command == "GAME_WIN":
                    self.my_turn = False
                    self.stop_timer()
                    self.handle_game_result("Bạn đã chiến thắng!")

                elif command == "GAME_LOSE":
                    self.my_turn = False
                    self.stop_timer()
                    self.handle_game_result("Bạn đã thua!")

        finally:
            self.root.after(100, self.process_messages)

    def start_timer(self, remaining_time):
        self.stop_timer()
        self.remaining_time = remaining_time
        self.update_timer()

    def update_timer(self):
        if self.my_turn and self.remaining_time > 0:
            self.status_bar.config(text=f"Tới lượt bạn! Còn {self.remaining_time} giây.")
            self.remaining_time -= 1
            self.timer_id = self.root.after(1000, self.update_timer)
        elif self.my_turn and self.remaining_time <= 0:
            self.my_turn = False
            self.status_bar.config(text="Hết giờ!")
    
    def stop_timer(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    def handle_game_result(self, result_text):
        messagebox.showinfo("Kết thúc", result_text)
        self.game_started = False
        self.my_turn = False
        # Hiện lại màn hình chờ để chơi ván mới
        self.show_waiting_screen()

    def handle_game_result_offline(self, winner):
        message = ""
        if winner == 'O won': message = "Chúc mừng, bạn đã thắng!"
        elif winner == 'X won': message = "Rất tiếc, máy đã thắng!"
        
        self.root.after(200, lambda: self.show_play_again_dialog(message))

    def show_play_again_dialog(self, message):
        messagebox.showinfo("Kết thúc", message)
        if messagebox.askyesno("Chơi lại?", "Bạn có muốn chơi lại không?"):
            self.game.reset_board()
            self.game_board.reset()
            self.status_bar.config(text="Chế độ Offline: Tới lượt bạn.")
        else:
            self.create_mode_selection_ui() # Quay về màn hình chính

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChessboardApp(root)
    root.mainloop()
