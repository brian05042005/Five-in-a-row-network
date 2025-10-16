# File: caro_game.py
import random

class CaroGame:
    def __init__(self):
        """
        Khởi tạo logic game, bao gồm bàn cờ.
        - 0: Ô trống
        - 1: Quân O (người chơi 1)
        - 2: Quân X (người chơi 2)
        """
        self.board = [[0 for _ in range(25)] for _ in range(25)]

    def make_move(self, y, x, player_id):
        """Thực hiện một nước đi trên bàn cờ."""
        if self.is_in(y, x) and self.board[y][x] == 0:
            self.board[y][x] = player_id
            return True
        return False

    def reset_board(self):
        """Làm mới lại bàn cờ, tất cả các ô về 0."""
        for row in self.board:
            for i in range(len(self.board)):
                row[i] = 0

    # ===================================================================
    # CÁC HÀM KIỂM TRA LOGIC (is_win, is_in, ...)
    # Tất cả các hàm này được chuyển từ file main.py cũ vào đây.
    # ===================================================================

    def is_in(self, y, x):
        """Kiểm tra tọa độ có nằm trong bàn cờ không."""
        return 0 <= y < len(self.board) and 0 <= x < len(self.board[0])

    def is_empty(self):
      """Kiểm tra bàn cờ có trống không."""
      for subarray in self.board:
        if not all(element == 0 for element in subarray):
          return False
      return True

    def is_win(self):
        """Kiểm tra trạng thái bàn cờ (X thắng/ O thắng/ đang tiếp tục chơi)."""
        black_O = self.score_of_col(self.board, 1)
        white_X = self.score_of_col(self.board, 2)

        self.sum_sumcol_values(black_O)
        self.sum_sumcol_values(white_X)

        if 5 in black_O and black_O[5] == 1:
            return 'O won'
        elif 5 in white_X and white_X[5] == 1:
            return 'X won'

        if sum(black_O.values()) == black_O[-1] and sum(white_X.values()) == white_X[-1] or self.possible_moves(self.board) == []:
            return 'Draw'
        return 'continue playing'

    # ===================================================================
    # THUẬT TOÁN AI (best_move và các hàm hỗ trợ)
    # Toàn bộ khối AI được chuyển vào đây.
    # ===================================================================

    def march(self, board, y, x, dy, dx, length):
        yf = y + length * dy
        xf = x + length * dx
        while not self.is_in(yf, xf):
            yf -= dy
            xf -= dx
        return yf, xf

    def score_ready(self, scorecol):
        sumcol = {0: {}, 1: {}, 2: {}, 3: {}, 4: {}, 5: {}, -1: {}}
        for key in scorecol:
            for score in scorecol[key]:
                if key in sumcol[score]:
                    sumcol[score][key] += 1
                else:
                    sumcol[score][key] = 1
        return sumcol

    def sum_sumcol_values(self, sumcol):
        for key in sumcol:
            if key == 5:
                sumcol[5] = int(1 in sumcol[5].values())
            else:
                sumcol[key] = sum(sumcol[key].values())

    def score_of_list(self, lis, col):
        blank = lis.count(0)
        filled = lis.count(col)
        if blank + filled < 5:
            return -1
        elif blank == 5:
            return 0
        else:
            return filled

    def row_to_list(self, board, y, x, dy, dx, yf, xf):
        row = []
        while y != yf + dy or x != xf + dx:
            row.append(board[y][x])
            y += dy
            x += dx
        return row

    def score_of_row(self, board, cordi, dy, dx, cordf, col):
        colscores = []
        y, x = cordi
        yf, xf = cordf
        row = self.row_to_list(board, y, x, dy, dx, yf, xf)
        for start in range(len(row) - 4):
            score = self.score_of_list(row[start:start + 5], col)
            colscores.append(score)
        return colscores

    def score_of_col(self, board, col):
        f = len(board)
        scores = {(0, 1): [], (-1, 1): [], (1, 0): [], (1, 1): []}
        for start in range(len(board)):
            scores[(0, 1)].extend(self.score_of_row(board, (start, 0), 0, 1, (start, f - 1), col))
            scores[(1, 0)].extend(self.score_of_row(board, (0, start), 1, 0, (f - 1, start), col))
            scores[(1, 1)].extend(self.score_of_row(board, (start, 0), 1, 1, (f - 1, f - 1 - start), col))
            scores[(-1, 1)].extend(self.score_of_row(board, (start, 0), -1, 1, (0, start), col))
            if start + 1 < len(board):
                scores[(1, 1)].extend(self.score_of_row(board, (0, start + 1), 1, 1, (f - 2 - start, f - 1), col))
                scores[(-1, 1)].extend(self.score_of_row(board, (f - 1, start + 1), -1, 1, (start + 1, f - 1), col))
        return self.score_ready(scores)

    def score_of_col_one(self, board, col, y, x):
        scores = {(0, 1): [], (-1, 1): [], (1, 0): [], (1, 1): []}
        scores[(0, 1)].extend(self.score_of_row(board, self.march(board, y, x, 0, -1, 4), 0, 1, self.march(board, y, x, 0, 1, 4), col))
        scores[(1, 0)].extend(self.score_of_row(board, self.march(board, y, x, -1, 0, 4), 1, 0, self.march(board, y, x, 1, 0, 4), col))
        scores[(1, 1)].extend(self.score_of_row(board, self.march(board, y, x, -1, -1, 4), 1, 1, self.march(board, y, x, 1, 1, 4), col))
        scores[(-1, 1)].extend(self.score_of_row(board, self.march(board, y, x, -1, 1, 4), 1, -1, self.march(board, y, x, 1, -1, 4), col))
        return self.score_ready(scores)

    def possible_moves(self, board):
        taken = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (-1, 1), (1, -1)]
        cord = {}
        for i in range(len(board)):
            for j in range(len(board)):
                if board[i][j] != 0:
                    taken.append((i, j))
        for direction in directions:
            dy, dx = direction
            for coord in taken:
                y, x = coord
                for length in [1, 2, 3, 4]:
                    move = self.march(board, y, x, dy, dx, length)
                    if move not in taken and move not in cord:
                        cord[move] = False
        return cord

    def TF34score(self, score3, score4):
        for key4 in score4:
            if score4[key4] >= 1:
                for key3 in score3:
                    if key3 != key4 and score3[key3] >= 2:
                        return True
        return False

    def stupid_score(self, board, col, anticol, y, x):
        M = 1000
        res, adv, dis = 0, 0, 0
        board[y][x] = col
        sumcol = self.score_of_col_one(board, col, y, x)
        a = self.winning_situation(sumcol)
        adv += a * M
        self.sum_sumcol_values(sumcol)
        adv += sumcol[-1] + sumcol[1] + 4 * sumcol[2] + 8 * sumcol[3] + 16 * sumcol[4]
        board[y][x] = anticol
        sumanticol = self.score_of_col_one(board, anticol, y, x)
        d = self.winning_situation(sumanticol)
        dis += d * (M - 100)
        self.sum_sumcol_values(sumanticol)
        dis += sumanticol[-1] + sumanticol[1] + 4 * sumanticol[2] + 8 * sumanticol[3] + 16 * sumanticol[4]
        res = adv + dis
        board[y][x] = 0
        return res

    def winning_situation(self, sumcol):
        if 1 in sumcol[5].values():
            return 5
        elif len(sumcol[4]) >= 2 or (len(sumcol[4]) >= 1 and max(sumcol[4].values()) >= 2):
            return 4
        elif self.TF34score(sumcol[3], sumcol[4]):
            return 4
        else:
            score3 = sorted(sumcol[3].values(), reverse=True)
            if len(score3) >= 2 and score3[0] >= score3[1] >= 2:
                return 3
        return 0

    def best_move(self, col):
        """Trả lại nước đi tốt nhất cho quân cờ `col`."""
        if col == 2:
            anticol = 1
        else:
            anticol = 2
        movecol = (0, 0)
        maxscorecol = -float('inf')
        if self.is_empty():
            movecol = (random.randint(10, 14), random.randint(10, 14))
        else:
            moves = self.possible_moves(self.board)
            for move in moves:
                y, x = move
                scorecol = self.stupid_score(self.board, col, anticol, y, x)
                if scorecol > maxscorecol:
                    maxscorecol = scorecol
                    movecol = move
        return movecol