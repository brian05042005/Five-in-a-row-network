import tkinter as tk
import os
import math

class GameBoardUI:
    def __init__(self, parent, size=25, cell_size=30):
        self.parent = parent
        self.size = size
        self.cell_size = cell_size
        self.margin = 25
        self.bg_color = "#fefaf5"
        self.grid_color = "#a07a48"
        self.hover_color = "#ffe5b4"
        self.shadow_color = "#d8b887"

        self.board_state = [[0]*size for _ in range(size)]
        self.winning_line = None
        self.hover_rect = None
        self.move_callback = None

        w = (size-1)*cell_size + 2*self.margin
        h = w
        self.canvas = tk.Canvas(parent, width=w, height=h, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(padx=10, pady=10)

        self.photo_refs = {}
        self.load_assets()

        # tạo bóng đổ cho khung bàn
        self.canvas.create_rectangle(
            self.margin-10, self.margin-10, w-self.margin+10, h-self.margin+10,
            fill=self.shadow_color, outline="", tags="shadow"
        )
        self.canvas.create_rectangle(
            self.margin, self.margin, w-self.margin, h-self.margin,
            fill=self.bg_color, outline="#b08d57", width=3, tags="frame"
        )

        self.draw_grid()
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_hover)
        self.canvas.bind("<Leave>", self.on_leave)

    def load_assets(self):
        base = os.path.join(os.getcwd(), "assets")
        for name in ("x.png", "o.png"):
            p = os.path.join(base, name)
            if os.path.exists(p):
                self.photo_refs[name[0]] = tk.PhotoImage(file=p)

    def draw_grid(self):
        for i in range(self.size):
            x = self.margin + i*self.cell_size
            self.canvas.create_line(x, self.margin, x, self.margin+(self.size-1)*self.cell_size,
                                    fill=self.grid_color)
            y = self.margin + i*self.cell_size
            self.canvas.create_line(self.margin, y, self.margin+(self.size-1)*self.cell_size, y,
                                    fill=self.grid_color)

    def coord_center(self, row, col):
        x = self.margin + col*self.cell_size
        y = self.margin + row*self.cell_size
        return x, y

    def on_click(self, e):
        c = self.pixel_to_cell(e.x, e.y)
        if c and self.move_callback:
            r, c = c
            self.move_callback(r, c)

    def on_hover(self, e):
        c = self.pixel_to_cell(e.x, e.y)
        if not c: return
        r, c = c
        x1 = self.margin + c*self.cell_size - self.cell_size/2
        y1 = self.margin + r*self.cell_size - self.cell_size/2
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        if self.hover_rect:
            self.canvas.delete(self.hover_rect)
        self.hover_rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline="#ff9f40", width=2)

    def on_leave(self, e):
        if self.hover_rect:
            self.canvas.delete(self.hover_rect)
            self.hover_rect = None

    def pixel_to_cell(self, x, y):
        x -= self.margin
        y -= self.margin
        col = round(x/self.cell_size)
        row = round(y/self.cell_size)
        if 0 <= row < self.size and 0 <= col < self.size:
            return row, col
        return None

    def place_piece(self, row, col, pid):
        if self.board_state[row][col] != 0: return
        self.board_state[row][col] = pid
        x, y = self.coord_center(row, col)
        r = self.cell_size*0.4
        tag = f"piece_{row}_{col}"
        if pid == 1 and "x" in self.photo_refs:
            self.canvas.create_image(x, y, image=self.photo_refs["x"], tags=("piece", tag))
        elif pid == 2 and "o" in self.photo_refs:
            self.canvas.create_image(x, y, image=self.photo_refs["o"], tags=("piece", tag))
        else:
            color = "#222" if pid==1 else "#eee"
            outline = "#000" if pid==2 else ""
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline=outline, tags=("piece", tag))

    def draw_winning_line(self, start, end):
        x1, y1 = self.coord_center(*start)
        x2, y2 = self.coord_center(*end)
        self.winning_line = self.canvas.create_line(x1, y1, x2, y2, fill="#e63946", width=5)

    def reset(self):
        self.canvas.delete("piece")
        if self.winning_line:
            self.canvas.delete(self.winning_line)
        self.board_state = [[0]*self.size for _ in range(self.size)]
