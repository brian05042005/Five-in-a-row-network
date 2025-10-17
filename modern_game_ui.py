"""
Modern Game Board UI - Lớp giao diện bàn cờ hiện đại
Được tách ra để dễ quản lý và tái sử dụng.
"""
import tkinter as tk
from tkinter import ttk

class GameBoardUI:
    """Giao diện bàn cờ hiện đại với đồ họa được cải thiện."""

    def __init__(self, parent, size=25, cell_size=30):
        self.parent = parent
        self.size = size
        self.cell_size = cell_size
        self.margin = 30 # Tăng lề để đẹp hơn

        # Bảng màu hiện đại
        self.board_color = "#E1C699"  # Màu gỗ sáng
        self.line_color = "#5C3D2E"   # Màu gỗ tối
        self.player1_color = "#2C3E50" # Màu đen mờ
        self.player2_color = "#ECF0F1" # Màu trắng xám
        self.last_move_color = "#E74C3C"  # Màu đỏ cho dấu last move

        # Trạng thái giao diện
        self.board_state = [[0 for _ in range(size)] for _ in range(size)]
        self.last_move_marker = None
        self.winning_line = None
        
        # Callback để thông báo cho lớp cha khi có nước đi
        self.move_callback = None
        
        # Khởi tạo canvas
        canvas_size = (self.size - 1) * self.cell_size + 2 * self.margin
        self.canvas = tk.Canvas(
            parent,
            width=canvas_size,
            height=canvas_size,
            bg=self.board_color,
            highlightthickness=0
        )
        self.canvas.pack(expand=True, padx=10, pady=10)
        
        self.draw_board()
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def draw_board(self):
        """Vẽ lưới bàn cờ."""
        self.canvas.delete("grid")
        for i in range(self.size):
            x_start = self.margin
            y_start = self.margin + i * self.cell_size
            x_end = self.margin + (self.size - 1) * self.cell_size
            y_end = y_start
            self.canvas.create_line(x_start, y_start, x_end, y_end, fill=self.line_color, width=1, tags="grid")

            x_start, y_start = self.margin + i * self.cell_size, self.margin
            x_end, y_end = x_start, self.margin + (self.size - 1) * self.cell_size
            self.canvas.create_line(x_start, y_start, x_end, y_end, fill=self.line_color, width=1, tags="grid")

        # Vẽ các điểm sao (star points) cho đẹp
        star_points = [(3, 3), (3, self.size-4), (self.size-4, 3), (self.size-4, self.size-4), (self.size//2, self.size//2)]
        for r, c in star_points:
            if 0 <= r < self.size and 0 <= c < self.size:
                x = self.margin + c * self.cell_size
                y = self.margin + r * self.cell_size
                self.canvas.create_oval(x-4, y-4, x+4, y+4, fill=self.line_color, outline="", tags="grid")

    def get_board_coords(self, event):
        """Chuyển đổi tọa độ pixel trên canvas sang tọa độ (hàng, cột) của bàn cờ."""
        x, y = event.x - self.margin, event.y - self.margin
        row = round(y / self.cell_size)
        col = round(x / self.cell_size)
        if 0 <= row < self.size and 0 <= col < self.size:
            return row, col
        return None

    def on_canvas_click(self, event):
        """Xử lý sự kiện click chuột trên bàn cờ."""
        coords = self.get_board_coords(event)
        if coords and self.move_callback:
            row, col = coords
            # Gọi callback để lớp cha xử lý logic
            self.move_callback(row, col)

    def place_piece(self, row, col, player_id):
        """Vẽ một quân cờ lên bàn cờ."""
        if self.board_state[row][col] != 0:
            return
        
        self.board_state[row][col] = player_id
        x = self.margin + col * self.cell_size
        y = self.margin + row * self.cell_size
        radius = self.cell_size * 0.45

        color = self.player1_color if player_id == 1 else self.player2_color
        outline_color = self.player1_color if player_id == 2 else "" # Quân trắng có viền đen
        
        self.canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            fill=color, outline=outline_color, width=1, tags="piece"
        )
        self.highlight_last_move(row, col)

    def highlight_last_move(self, row, col):
        """Đánh dấu nước đi cuối cùng."""
        if self.last_move_marker:
            self.canvas.delete(self.last_move_marker)
        
        x = self.margin + col * self.cell_size
        y = self.margin + row * self.cell_size
        radius = self.cell_size * 0.15
        
        self.last_move_marker = self.canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            fill=self.last_move_color, outline=""
        )

    def draw_winning_line(self, start_coords, end_coords):
        """Vẽ đường kẻ chiến thắng."""
        (start_row, start_col) = start_coords
        (end_row, end_col) = end_coords

        x1 = self.margin + start_col * self.cell_size
        y1 = self.margin + start_row * self.cell_size
        x2 = self.margin + end_col * self.cell_size
        y2 = self.margin + end_row * self.cell_size
        
        self.winning_line = self.canvas.create_line(x1, y1, x2, y2, fill="#D35400", width=5, capstyle=tk.ROUND)

    def reset(self):
        """Xóa toàn bộ bàn cờ để bắt đầu ván mới."""
        self.canvas.delete("piece")
        if self.last_move_marker:
            self.canvas.delete(self.last_move_marker)
            self.last_move_marker = None
        if self.winning_line:
            self.canvas.delete(self.winning_line)
            self.winning_line = None
        self.board_state = [[0 for _ in range(self.size)] for _ in range(self.size)]
