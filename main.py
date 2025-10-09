import tkinter as tk  # Import thư viện tkinter
import random
import time
import sys
import tkinter.messagebox as messagebox
from network import NetworkManager  #import class network
from tkinter import simpledialog, messagebox
import queue

class ChessboardApp:
    #biến cho biến trạng thái thắng/thua
    win = False
    #rows = cols, số hàng và số cột của bàn cờ
    ROWS_COLS = 100 
    #chiều dài của một ô
    PIXEL = 40
     # Khởi tạo mảng 2 chiều kích thước 25x25
    # 1 là quan O tuong trung cho nguoi choi
    # 2 la quan x tuong trung cho may
    # 0 la o chua duoc danh
    board = [[0 for _ in range(25)] for _ in range(25)]
    
    def __init__(self, root):

        self.root = root
        #Đặt tiêu đề cho cửa sổ gốc
        self.root.title("FiveinARow")
        # Đặt kích thước cửa sổ gốc là 1000x1000 pixel
        self.root.geometry("1000x1000")

        #Networking và trạng thái game online
        self.message_queue = queue.Queue()
        self.network = NetworkManager(self.message_queue)
        self.my_turn = False
        self.my_piece_id = 0 # Sẽ được server gán là 1 hoặc 2
        self.opponent_piece_id = 0
        self.timer_id = None
        self.remaining_time = 30
        self.username = ""
        self.game_started = False  

        #frame chính để chứa các widget
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        #tạo giao diện đăng nhập ban đầu
        self.create_login_ui()

        # Tạo một canvas với kích thước 1000x1000 pixel và màu nền là "Dodger blue"
        self.canvas = tk.Canvas(root, width=1000, height=1000, bg="White")  
        self.canvas.pack()

        # Gọi hàm vẽ bàn cờ với kích thước ô là 40 pixel và 25x25 
        self.draw_chessboard(self.PIXEL, self.ROWS_COLS)  
        
    # Các hàm networking và giao diện
    def create_login_ui(self):
        """Tạo giao diện cho việc đăng nhập."""
        self.login_frame = tk.Frame(self.main_frame)
        self.login_frame.pack(pady=200)

        tk.Label(self.login_frame, text="Your Name:", font=("Arial", 14)).pack(pady=5)
        self.name_entry = tk.Entry(self.login_frame, font=("Arial", 14))
        self.name_entry.pack(pady=5)

        tk.Label(self.login_frame, text="Server IP:", font=("Arial", 14)).pack(pady=5)
        self.ip_entry = tk.Entry(self.login_frame, font=("Arial", 14))
        self.ip_entry.insert(0, "127.0.0.1") # IP mặc định là localhost
        self.ip_entry.pack(pady=5)

        connect_button = tk.Button(self.login_frame, text="Connect and Find Match", font=("Arial", 16), command=self.connect_to_server)
        connect_button.pack(pady=20)

    def connect_to_server(self):
        """Kết nối tới server và gửi thông tin đăng nhập."""
        self.username = self.name_entry.get()
        ip = self.ip_entry.get()
        if not self.username or not ip:
            messagebox.showerror("Error", "Please enter your name and server IP.")
            return

        if self.network.connect(ip, 13000):
            self.network.send_message(f"LOGIN|{self.username}")
            # Bắt đầu kiểm tra message queue
            self.root.after(100, self.process_messages)
        else:
            messagebox.showerror("Error", "Could not connect to the server.")

    def setup_game_ui(self):
        """Thiết lập giao diện chơi game sau khi kết nối thành công."""
        self.login_frame.destroy()

        # Thanh trạng thái
        self.status_bar = tk.Label(self.main_frame, text="Waiting for opponent...", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Canvas chơi game
        self.canvas = tk.Canvas(self.main_frame, width=1000, height=1000, bg="White")
        self.canvas.pack()
        self.draw_chessboard(self.PIXEL, self.ROWS_COLS)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def process_messages(self):
        """Xử lý các tin nhắn từ server trong queue."""
        try:
            while not self.message_queue.empty():
                message = self.message_queue.get_nowait()
                print(f"Processing message: {message}")
                parts = message.split('|')
                command = parts[0]

                if command == "LOGIN_SUCCESS":
                    messagebox.showinfo("Success", "Connected!")
                    self.setup_game_ui()
                    self.status_bar.config(text="Waiting for an opponent...")

                elif command == "GAME_START":
                    opponent = parts[1]
                    self.my_piece_id = int(parts[2])
                    self.game_started = True
                    self.reset_board_zero(self.board)
                    self.refresh_graphics()
                    piece_type = "O (Blue)" if self.my_piece_id == 1 else "X (Red)"
                    messagebox.showinfo("Game On!", f"Match started against {opponent}. You are {piece_type}")

                elif command == "YOUR_TURN":
                    self.my_turn = True
                    self.remaining_time = int(parts[1])
                    self.start_timer()
                
                # <<< THAY ĐỔI LỚN Ở ĐÂY: Thay OPPONENT_MOVE bằng UPDATE_BOARD
                elif command == "UPDATE_BOARD":
                    coords = parts[1].split(',')
                    x, y = int(coords[0]), int(coords[1])
                    piece_id = int(parts[2])

                    # Cập nhật lại bảng logic và vẽ
                    if self.board[y][x] == 0:
                        self.board[y][x] = piece_id
                        if piece_id == 1: # Quân O
                            self.draw_circle(18, "blue", x * self.PIXEL + 20, y * self.PIXEL + 20)
                        else: # Quân X
                            self.draw_cross(18, "red", x * self.PIXEL + 20, y * self.PIXEL + 20)
                    
                    # Sau khi vẽ, kiểm tra thắng thua cục bộ
                    winner = self.is_win(self.board)
                    if winner == 'O won' and self.my_piece_id == 1:
                        self.network.send_message("GAME_WIN")
                    elif winner == 'X won' and self.my_piece_id == 2:
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
            self.status_bar.config(text="Time's up! You lose.")
            # Server sẽ tự động xử lý khi hết giờ, nhưng client cũng có thể gửi tin nhắn
            # self.network.send_message("TIMEOUT")

    def stop_timer(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    #các hàm gameplay
    def on_canvas_click(self, event):
        """Xử lý khi người chơi click lên bàn cờ."""
        if not self.my_turn or not self.game_started:
            return

        col, row = self.getindexposition(event.x, event.y)

        if self.board[row][col] == 0:
            # Chỉ gửi nước đi lên server, KHÔNG vẽ gì cả
            self.network.send_message(f"MOVE|{col},{row}")
            
            # Vô hiệu hóa lượt đi ngay lập tức để tránh click nhiều lần
            self.my_turn = False
            self.stop_timer()
            self.status_bar.config(text="Waiting for opponent's move...")

    def handle_game_result(self, winner_text):
        messagebox.showinfo("Game Over", winner_text)
        # Có thể thêm logic hỏi chơi lại và gửi yêu cầu rematch tới server
        self.game_started = False
        # Không thoát chương trình, chỉ chờ ván mới
        self.status_bar.config(text="Game over. Waiting for a new challenge.")


    def refresh_graphics(self):
        if hasattr(self, 'canvas'):
            self.canvas.delete("all")
            self.draw_chessboard(self.PIXEL, self.ROWS_COLS)

    def draw_chessboard(self, size, n):
        for i in range(n):
            for j in range(n):
                x, y = i * size, j * size
                self.canvas.create_rectangle(x, y, x + size, y + size, outline="black", width=1)

#Các hàm logic cũ (giữ lại để check thắng)
 #Check the status of the chess board
#kiểm tra tọa độ có nằm trong bàn cờ không
    def is_in(self, board, y, x):
        return 0 <= y < len(self.board) and 0 <= x < len(self.board)
    
    #kiểm tra bàn cờ có rỗng không
    def is_empty(self, array):
      # Duyệt qua tất cả các mảng con trong mảng cha
      for subarray in array:
        # Kiểm tra xem tất cả các phần tử trong mảng con có bằng 0 hay không
        if not all(element == 0 for element in subarray):
          # Nếu có phần tử khác 0, trả về False
          return False
      # Nếu không có phần tử khác 0, trả về True
      return True

    #kiếm tra trạng thái bàn cờ (X thắng/ O thắng/ đang tiếp tục chơi)
    def is_win(self, board):
        #
        black_O = self.score_of_col(board, 1) 
        white_X = self.score_of_col(board, 2)

        self.sum_sumcol_values(black_O)
        self.sum_sumcol_values(white_X)

        if 5 in black_O and black_O[5] == 1:
            #self.highlight_winning_row(board, black_O, 1)
            return 'O won'
        elif 5 in white_X and white_X[5] == 1:
            #self.highlight_winning_row(board, white_X, 2)
            return 'X won'

        if sum(black_O.values()) == black_O[-1] and sum(white_X.values()) == white_X[-1] or self.possible_moves(board) == []:
            return 'Draw'
        return 'continue playing'

    def reset_board_zero(self,board):
        for row in board:
            for i in range(len(board)):
                row[i] = 0 

#Graphic 
    def handle_click(self, event):                              
        x = event.x
        y = event.y 
        x,y = self.getindexposition(x,y)

        self.draw_circle(18,"blue",x*40+20,y*40+20)
        self.board[y][x]=1
        x_next, y_next = self.best_move(self.board,2)
        self.board[x_next][y_next]=2
        self.draw_cross(18,'red',y_next*40+20,x_next*40+20)
        
        winner = self.is_win(self.board)
        if winner != 'continue playing':
            self.handle_game_result(winner)
               
    def draw_chessboard(self, size, n):
        for i in range(n):
            for j in range(n):
                color = "black" #Đường viền màu đen
                x = i * size  # Tọa độ x của ô
                y = j * size  # Tọa độ y của ô
                self.draw_square(size, color, x, y)  # Vẽ ô vuông

    def draw_square(self, size, color, x, y):
    # Phương thức vẽ một ô vuông trên bàn cờ
    # size: kích thước của ô
    # color: màu sắc của ô
    # x, y: tọa độ (x, y) của ô
     self.canvas.create_rectangle(x, y, x + size, y + size, outline=color, width=2)  

    def draw_cross(self, size,color, x, y):
       self.canvas.create_line(x - size, y - size, x + size, y + size, fill=color, width=5) # Đường thẳng từ trên trái xuống dưới phải
       self.canvas.create_line(x + size, y - size, x - size, y + size, fill=color, width=5) # Đường thẳng từ trên phải xuống dưới trái
       
    def draw_circle(self, size,color, x, y):
    # Draw a black circle with the given parameters
     self.canvas.create_oval(x - size, y - size, x + size, y + size, outline="black", width = 3)

    def getindexposition(self, x, y): #chuyen doi toa do click chuot sang toa do tren o co
        index_x = x // 40
        index_y = y // 40
        return index_x, index_y
    
    def refresh_graphics(self):
        self.canvas.delete("all")  # Xóa tất cả các hình ảnh trên canvas
        self.draw_chessboard(40, 25)  # Vẽ lại bàn cờ với kích thước ô là 40 và 25 ô
        
    def handle_game_result(self, winner):
        if winner == 'O won':
            messagebox.showinfo("Game Over", "Người chơi O đã chiến thắng!")
        elif winner == 'X won':
            messagebox.showinfo("Game Over", "Người chơi X đã chiến thắng!")
        elif winner == 'Draw':
            messagebox.showinfo("Game Over", "Trận đấu kết thúc với kết quả hòa!")
        else:
            return

        play_again = messagebox.askyesno("Chơi lại?", "Bạn có muốn chơi lại từ đầu không?")
        if play_again:
            self.reset_board_zero(self.board)
            self.refresh_graphics()
        else:
            sys.exit()
           
   
   #AI
    
    def march(self,board,y,x,dy,dx,length):
        '''
        tìm vị trí xa nhất trong dy,dx trong khoảng length

        '''
        yf = y + length*dy 
        xf = x + length*dx
        # chừng nào yf,xf không có trong board
        while not self.is_in(board,yf,xf):
            yf -= dy
            xf -= dx
        
        return yf,xf
    
    def score_ready(self, scorecol):
        '''
        Khởi tạo hệ thống điểm

        '''
        sumcol = {0: {},1: {},2: {},3: {},4: {},5: {},-1: {}}
        for key in scorecol:
            for score in scorecol[key]:
                if key in sumcol[score]:
                    sumcol[score][key] += 1
                else:
                    sumcol[score][key] = 1
            
        return sumcol
    
    def sum_sumcol_values(self,sumcol):
        '''
        hợp nhất điểm của mỗi hướng
        '''
    
        for key in sumcol:
            if key == 5:
                sumcol[5] = int(1 in sumcol[5].values())
            else:
                sumcol[key] = sum(sumcol[key].values())
                
    def score_of_list(self,lis,col):
    
        blank = lis.count(0)
        filled = lis.count(col)
    
        if blank + filled < 5:
            return -1
        elif blank == 5:
            return 0
        else:
            return filled
        
    def row_to_list(self,board,y,x,dy,dx,yf,xf):
        '''
        trả về list của y,x từ yf,xf
    
        '''
        row = []
        while y != yf + dy or x !=xf + dx:
            row.append(board[y][x])
            y += dy
            x += dx
        return row
    
    def score_of_row(self,board,cordi,dy,dx,cordf,col):
        '''
        trả về một list với mỗi phần tử đại diện cho số điểm của 5 khối

        '''
        colscores = []
        y,x = cordi
        yf,xf = cordf
        row = self.row_to_list(board,y,x,dy,dx,yf,xf)
        for start in range(len(row)-4):
            score = self.score_of_list(row[start:start+5],col)
            colscores.append(score)
    
        return colscores
    
    def score_of_col(self,board,col):
        '''
        tính toán điểm số mỗi hướng của column dùng cho is_win;
        '''

        f = len(board)
        #scores của 4 hướng đi
        scores = {(0,1):[],(-1,1):[],(1,0):[],(1,1):[]}
        for start in range(len(board)):
            scores[(0,1)].extend(self.score_of_row(board,(start, 0), 0, 1,(start,f-1), col))
            scores[(1,0)].extend(self.score_of_row(board,(0, start), 1, 0,(f-1,start), col))
            scores[(1,1)].extend(self.score_of_row(board,(start, 0), 1,1,(f-1,f-1-start), col))
            scores[(-1,1)].extend(self.score_of_row(board,(start,0), -1, 1,(0,start), col))
        
            if start + 1 < len(board):
                scores[(1,1)].extend(self.score_of_row(board,(0, start+1), 1, 1,(f-2-start,f-1), col)) 
                scores[(-1,1)].extend(self.score_of_row(board,(f -1 , start + 1), -1,1,(start+1,f-1), col))
            
        return self.score_ready(scores)
    
    def score_of_col_one(self, board,col,y,x):
        '''
        trả lại điểm số của column trong y,x theo 4 hướng,
        key: điểm số khối đơn vị đó -> chỉ ktra 5 khối thay vì toàn bộ
        '''
    
        scores = {(0,1):[],(-1,1):[],(1,0):[],(1,1):[]}
    
        scores[(0,1)].extend(self.score_of_row(board,self.march(board,y,x,0,-1,4), 0, 1,self.march(board,y,x,0,1,4), col))
    
        scores[(1,0)].extend(self.score_of_row(board,self.march(board,y,x,-1,0,4), 1, 0,self.march(board,y,x,1,0,4), col))
    
        scores[(1,1)].extend(self.score_of_row(board,self.march(board,y,x,-1,-1,4), 1, 1,self.march(board,y,x,1,1,4), col))

        scores[(-1,1)].extend(self.score_of_row(board,self.march(board,y,x,-1,1,4), 1,-1,self.march(board,y,x,1,-1,4), col))
    
        return self.score_ready(scores)
    
    def possible_moves(self,board):  
        '''
        khởi tạo danh sách tọa độ có thể có tại danh giới các nơi đã đánh phạm vi 3 đơn vị
        '''
        #mảng taken lưu giá trị của người chơi và của máy trên bàn cờ
        taken = []
        # mảng directions lưu hướng đi (8 hướng)
        directions = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(-1,-1),(-1,1),(1,-1)]
        # cord: lưu các vị trí không đi 
        cord = {}
    
        for i in range(len(board)):
            for j in range(len(board)):
                if board[i][j] != 0:
                    taken.append((i,j))
        ''' duyệt trong hướng đi và mảng giá trị trên bàn cờ của người chơi và máy, kiểm tra nước không thể đi(trùng với 
        nước đã có trên bàn cờ)
        '''
        for direction in directions:
            dy,dx = direction
            for coord in taken:
                y,x = coord
                for length in [1,2,3,4]:
                    move = self.march(board,y,x,dy,dx,length)
                    if move not in taken and move not in cord:
                        cord[move]=False
        return cord
    
    def TF34score(self, score3,score4):
        '''
        trả lại trường hợp chắc chắn có thể thắng(4 ô liên tiếp)
        '''
        for key4 in score4:
            if score4[key4] >=1:
                for key3 in score3:
                    if key3 != key4 and score3[key3] >=2:
                            return True
        return False
    
    def stupid_score(self, board,col,anticol,y,x):
        '''
        cố gắng di chuyển y,x
        trả về điểm số tượng trưng lợi thế 
        '''
    
        global colors
        M = 1000
        res,adv, dis = 0, 0, 0
    
        #tấn công
        board[y][x]=col
        #draw_stone(x,y,colors[col])
        sumcol = self.score_of_col_one(board,col,y,x)       
        a = self.winning_situation(sumcol)
        adv += a * M
        self.sum_sumcol_values(sumcol)
        #{0: 0, 1: 15, 2: 0, 3: 0, 4: 0, 5: 0, -1: 0}
        adv +=  sumcol[-1] + sumcol[1] + 4*sumcol[2] + 8*sumcol[3] + 16*sumcol[4]
    
        #phòng thủ
        board[y][x]=anticol
        sumanticol = self.score_of_col_one(board,anticol,y,x)  
        d = self.winning_situation(sumanticol)
        dis += d * (M-100)
        self.sum_sumcol_values(sumanticol)
        dis += sumanticol[-1] + sumanticol[1] + 4*sumanticol[2] + 8*sumanticol[3] + 16*sumanticol[4]

        res = adv + dis
    
        board[y][x]=0
        return res
    
    def winning_situation(self,sumcol):
        '''
        trả lại tình huống chiến thắng dạng như:
        {0: {}, 1: {(0, 1): 4, (-1, 1): 3, (1, 0): 4, (1, 1): 4}, 2: {}, 3: {}, 4: {}, 5: {}, -1: {}}
        1-5 lưu điểm có độ nguy hiểm từ thấp đến cao,
        -1 là rơi vào trạng thái tồi, cần phòng thủ
        '''
    
        if 1 in sumcol[5].values():
            return 5
        elif len(sumcol[4])>=2 or (len(sumcol[4])>=1 and max(sumcol[4].values())>=2):
            return 4
        elif self.TF34score(sumcol[3],sumcol[4]):
            return 4
        else:
            score3 = sorted(sumcol[3].values(),reverse = True)
            if len(score3) >= 2 and score3[0] >= score3[1] >= 2:
                return 3
        return 0

    def best_move(self,board,col):
        '''
        trả lại điểm số của mảng trong lợi thế của từng màu
        '''
        if col == 2:
            anticol = 1
        else:
            anticol = 2
        
        movecol = (0,0)
        maxscorecol = -2
        # kiểm tra nếu bàn cờ rỗng thì cho vị trí random nếu không thì đưa ra giá trị trên bàn cờ nên đi 
        if self.is_empty(board):
            movecol = ( int((len(board))*random.random()),int((len(board[0]))*random.random()))
        else:
            moves = self.possible_moves(board)

            for move in moves:
                y,x = move
                if maxscorecol == -2:
                    scorecol=self.stupid_score(board,col,anticol,y,x)
                    maxscorecol = scorecol
                    movecol = move
                else:
                    scorecol=self.stupid_score(board,col,anticol,y,x)
                    if scorecol > maxscorecol:
                        maxscorecol = scorecol
                        movecol = move
        return movecol

if __name__ == "__main__":
    root = tk.Tk()  # Khởi tạo cửa sổ gốc
    app = ChessboardApp(root)  # Tạo đối tượng ChessboardApp
    app.canvas.bind("<Button-1>", app.handle_click)
    root.mainloop()  # Bắt đầu vòng lặp chính của ứng dụng