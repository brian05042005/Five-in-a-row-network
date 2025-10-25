# caro_gui.py (phiên bản đã fix kiểm tra thắng)
import tkinter as tk
from tkinter import ttk, messagebox
import queue
from network import NetworkManager
from main import CaroGame
from modern_game_ui import GameBoardUI

class ChessboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Five in a Row")
        self.root.configure(bg="#F0F0F0")

        style = ttk.Style()
        style.theme_use('clam')

        self.game = CaroGame()
        self.network = NetworkManager(queue.Queue())
        self.message_queue = self.network.message_queue

        self.my_turn = False
        self.my_piece_id = 0
        self.username = ""
        self.opponent_name = ""
        self.game_started = False
        self.timer_id = None

        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_mode_selection_ui()

    # ---------- UI chọn chế độ ----------
    def create_mode_selection_ui(self):
        self.clear_main_frame()
        self.mode_selection_frame = ttk.Frame(self.main_frame)
        self.mode_selection_frame.pack(expand=True)

        ttk.Label(self.mode_selection_frame, text="CHỌN CHẾ ĐỘ CHƠI", font=("Arial", 24, "bold")).pack(pady=20)
        ttk.Button(self.mode_selection_frame, text="Chơi Online", style='Accent.TButton', command=self.show_login_ui).pack(pady=10, ipady=5, ipadx=10)
        ttk.Button(self.mode_selection_frame, text="Chơi Offline (Với Máy)", command=self.start_offline_game).pack(pady=10, ipady=5, ipadx=10)

        s = ttk.Style()
        s.configure('Accent.TButton', font=('Arial', 14), background='#3498DB', foreground='white')
        s.map('Accent.TButton', background=[('active', '#2980B9')])

    # ---------- Kết nối ----------
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
        
        ttk.Label(self.login_frame, text="(Nhập IP máy chủ nếu chơi qua LAN)", font=("Arial", 9, "italic")).pack()
        ttk.Button(self.login_frame, text="Tìm trận", style='Accent.TButton', command=self.connect_to_server).pack(pady=20, ipady=5, ipadx=10)

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
            messagebox.showerror("Lỗi kết nối", f"Không thể kết nối đến {ip}:13000.")

    # ---------- Chế độ offline ----------
    def start_offline_game(self):
        self.root.title("Five in a Row - Offline")
        self.setup_game_view()
        self.status_bar.config(text="Chế độ Offline: Bạn đi trước (Quân Đen).")

    # ---------- Màn chờ ----------
    def show_waiting_screen(self):
        self.clear_main_frame()
        self.waiting_frame = ttk.Frame(self.main_frame)
        self.waiting_frame.pack(expand=True)
        ttk.Label(self.waiting_frame, text="Đang tìm đối thủ...", font=("Arial", 18)).pack()
        progress = ttk.Progressbar(self.waiting_frame, mode='indeterminate')
        progress.pack(pady=20, padx=50, fill=tk.X)
        progress.start()

    # ---------- Giao diện chính ----------
    def setup_game_view(self):
        self.clear_main_frame()

        container = ttk.Frame(self.main_frame)
        container.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        self.status_bar = ttk.Label(container, text="...", font=("Arial", 14, "italic"), anchor=tk.CENTER)
        self.status_bar.pack(pady=(0, 10), fill=tk.X)

        info = ttk.Frame(container)
        info.pack(fill=tk.X, pady=(0,6))
        self.you_label = ttk.Label(info, text=f"Bạn: {self.username}", font=("Arial", 11))
        self.vs_label = ttk.Label(info, text="VS", font=("Arial", 11, "bold"))
        self.opponent_label = ttk.Label(info, text=f"Đối thủ: {self.opponent_name}", font=("Arial", 11))
        self.you_label.pack(side=tk.LEFT, padx=10)
        self.vs_label.pack(side=tk.LEFT, padx=6)
        self.opponent_label.pack(side=tk.LEFT, padx=6)

        self.game_board = GameBoardUI(container, size=25, cell_size=28)
        self.game_board.move_callback = self.on_board_click

    # ---------- Xử lý nước đi ----------
    def on_board_click(self, row, col):
        if self.game.board[row][col] != 0: return

        if self.game_started:  # online
            if self.my_turn:
                self.network.send_message(f"MOVE|{col},{row}")
                self.game.make_move(row, col, self.my_piece_id)
                self.game_board.place_piece(row, col, self.my_piece_id)
                # Kiểm tra thắng
                winner, line = self.game.check_win_and_get_line(row, col)
                if winner:
                    self.game_board.draw_winning_line(line[0], line[1])
                    self.handle_game_result("Bạn đã chiến thắng!")
                    return
                self.my_turn = False
                self.stop_timer()
                self.status_bar.config(text="Đang chờ đối thủ...")
        else:
            self.handle_click_offline(row, col)

    def handle_click_offline(self, row, col):
        self.game.make_move(row, col, 1)
        self.game_board.place_piece(row, col, 1)
        winner, line = self.game.check_win_and_get_line(row, col)
        if winner:
            self.game_board.draw_winning_line(line[0], line[1])
            self.handle_game_result_offline(winner)
            return

        self.status_bar.config(text="Máy đang suy nghĩ...")
        self.root.after(500, self.execute_ai_turn)

    def execute_ai_turn(self):
        ai_row, ai_col = self.game.best_move(self.game.board)
        self.game.make_move(ai_row, ai_col, 2)
        self.game_board.place_piece(ai_row, ai_col, 2)
        winner, line = self.game.check_win_and_get_line(ai_row, ai_col)
        if winner:
            self.game_board.draw_winning_line(line[0], line[1])
            self.handle_game_result_offline(winner)
        else:
            self.status_bar.config(text="Tới lượt bạn.")

    # ---------- Xử lý message từ server ----------
    def process_messages(self):
        try:
            while not self.message_queue.empty():
                msg = self.message_queue.get_nowait()
                parts = msg.split('|')
                cmd = parts[0]

                if cmd == "GAME_START":
                    self.setup_game_view()
                    self.opponent_name = parts[1]
                    self.my_piece_id = int(parts[2])
                    self.game_started = True
                    self.you_label.config(text=f"Bạn: {self.username} ({'Đen' if self.my_piece_id==1 else 'Trắng'})")
                    self.opponent_label.config(text=f"Đối thủ: {self.opponent_name}")
                    messagebox.showinfo("Bắt đầu!", f"Bạn là quân {'Đen' if self.my_piece_id==1 else 'Trắng'}.")

                elif cmd == "YOUR_TURN":
                    self.my_turn = True
                    secs = int(parts[1]) if len(parts)>1 else 30
                    self.start_timer(secs)
                    self.status_bar.config(text="Tới lượt bạn!")

                elif cmd == "UPDATE_BOARD":
                    if len(parts) >= 3:
                        move = parts[1]; piece = int(parts[2])
                        col, row = map(int, move.split(','))
                        if self.game.board[row][col] == 0:
                            self.game.make_move(row, col, piece)
                            self.game_board.place_piece(row, col, piece)
                            winner, line = self.game.check_win_and_get_line(row, col)
                            if winner:
                                self.game_board.draw_winning_line(line[0], line[1])
                                # nếu mình không phải người vừa đánh thì mình thua
                                if piece != self.my_piece_id:
                                    self.handle_game_result("Đối thủ đã chiến thắng!")
                                else:
                                    self.handle_game_result("Bạn đã chiến thắng!")
                                return

                elif cmd == "GAME_WIN":
                    self.handle_game_result("Bạn đã chiến thắng!")
                elif cmd == "GAME_LOSE":
                    self.handle_game_result("Bạn đã thua!")

        finally:
            self.root.after(100, self.process_messages)

    # ---------- Timer ----------
    def start_timer(self, t):
        self.stop_timer()
        self.remaining_time = t
        self.update_timer()

    def update_timer(self):
        if self.my_turn and self.remaining_time > 0:
            self.status_bar.config(text=f"Tới lượt bạn! Còn {self.remaining_time}s.")
            self.remaining_time -= 1
            self.timer_id = self.root.after(1000, self.update_timer)
        elif self.my_turn and self.remaining_time <= 0:
            self.my_turn = False
            self.status_bar.config(text="Hết giờ!")

    def stop_timer(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    # ---------- Kết thúc ----------
    def handle_game_result(self, text):
        self.my_turn = False
        self.game_started = False
        self.stop_timer()
        messagebox.showinfo("Kết thúc", text)
        if messagebox.askyesno("Chơi lại?", "Bạn có muốn chơi lại không?"):
            self.game.reset_board()
            self.game_board.reset()
            self.status_bar.config(text="Chờ bắt đầu lại...")
            self.show_waiting_screen()
        else:
            self.create_mode_selection_ui()

    def handle_game_result_offline(self, winner):
        msg = "Chúc mừng, bạn đã thắng!" if winner == 'O won' else "Máy đã thắng!"
        messagebox.showinfo("Kết thúc", msg)
        if messagebox.askyesno("Chơi lại?", "Chơi lại không?"):
            self.game.reset_board()
            self.game_board.reset()
            self.status_bar.config(text="Tới lượt bạn.")
        else:
            self.create_mode_selection_ui()

    def clear_main_frame(self):
        for w in self.main_frame.winfo_children():
            w.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    ChessboardApp(root)
    root.mainloop()
