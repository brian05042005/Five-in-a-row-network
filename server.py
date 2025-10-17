import socket
import threading
import datetime

HOST = '127.0.0.1'  # IP của máy chủ, 127.0.0.1 là localhost
PORT = 13000

# Dùng dictionary để quản lý clients: { 'username': connection }
clients = {}
# Dùng dictionary để quản lý các cặp đấu: { 'player1_name': 'player2_name' }
matches = {}
player_roles = {}
# Khóa để bảo vệ việc truy cập đồng thời vào các biến toàn cục
lock = threading.Lock()

waiting_player = None

def save_match_history(player1, player2, winner):
    """Ghi lịch sử trận đấu vào file."""
    try:
        with open("match_history.log", "a", encoding="utf-8") as f:
            log_entry = f"{datetime.datetime.now()}: {player1} vs {player2} -> Winner: {winner}\n"
            f.write(log_entry)
            print(log_entry.strip())
    except Exception as e:
        print(f"Error saving match history: {e}")

def handle_client(conn, addr):
    print(f"New connection from {addr}")
    current_user = None
    try:
        login_data = conn.recv(1024).decode('utf-8')
        if not login_data:
            raise ConnectionAbortedError("Client disconnected before login")

        parts = login_data.strip().split('|')
        command = parts[0]
        global waiting_player, player_roles

        with lock:
            if command == "LOGIN":
                username = parts[1]
                if username in clients or username == waiting_player:
                    conn.sendall(b"LOGIN_FAIL|Username already taken")
                    current_user = None
                else:
                    clients[username] = conn
                    current_user = username
                    conn.sendall(b"LOGIN_SUCCESS")
                    print(f"User '{username}' logged in.")

                    if waiting_player is None:
                        waiting_player = current_user
                        print(f"'{current_user}' is now waiting for a match.")
                        conn.sendall(b"WAITING|Waiting for another player...")
                    else:
                        player1_name = waiting_player
                        player2_name = current_user
                        print(f"Match found: '{player1_name}' vs '{player2_name}'")
                        player1_conn = clients[player1_name]
                        player2_conn = clients[player2_name]
                        matches[player1_name] = player2_name
                        matches[player2_name] = player1_name

                        # <<< LƯU VAI TRÒ CỦA NGƯỜI CHƠI
                        player_roles[player1_name] = 1 # Player 1 là quân O
                        player_roles[player2_name] = 2 # Player 2 là quân X

                        waiting_player = None
                        player1_conn.sendall(f"GAME_START|{player2_name}|1".encode('utf-8'))
                        player2_conn.sendall(f"GAME_START|{player1_name}|2".encode('utf-8'))
                        player1_conn.sendall(b"YOUR_TURN|30")

        if current_user is None:
            conn.close()
            return

        while True:
            data = conn.recv(1024).decode('utf-8')
            if not data:
                break

            parts = data.strip().split('|')
            command = parts[0]

            with lock:
                if command == "MOVE":
                    if current_user in matches:
                        opponent_name = matches[current_user]
                        opponent_conn = clients[opponent_name]
                        move_data = parts[1]

                        # <<< SỬA LỖI LOGIC: Lấy quân cờ từ vai trò đã lưu
                        player_piece_id = player_roles.get(current_user)

                        if player_piece_id:
                            update_message = f"UPDATE_BOARD|{move_data}|{player_piece_id}".encode('utf-8')
                            conn.sendall(update_message)
                            opponent_conn.sendall(update_message)
                            opponent_conn.sendall(b"YOUR_TURN|30")

                elif command == "GAME_WIN":
                    if current_user in matches:
                        opponent_name = matches[current_user]
                        opponent_conn = clients[opponent_name]
                        opponent_conn.sendall(b"GAME_LOSE|You lose")
                        conn.sendall(b"GAME_WIN|You win")
                        save_match_history(current_user, opponent_name, current_user)

                        # <<< XÓA VAI TRÒ KHI KẾT THÚC GAME
                        del matches[current_user]
                        del matches[opponent_name]
                        if current_user in player_roles: del player_roles[current_user]
                        if opponent_name in player_roles: del player_roles[opponent_name]

    except Exception as e:
        print(f"Error handling client {current_user}: {e}")
    finally:
        with lock:
            if current_user:
                if current_user in clients:
                    del clients[current_user]
                if current_user in matches:
                    opponent_name = matches[current_user]
                    if opponent_name in clients:
                        clients[opponent_name].sendall(b"GAME_WIN|Opponent disconnected")
                        save_match_history(current_user, opponent_name, opponent_name)
                    del matches[current_user]
                    if opponent_name in matches:
                        del matches[opponent_name]
                    # <<< XÓA VAI TRÒ KHI NGẮT KẾT NỐI
                    if current_user in player_roles: del player_roles[current_user]
                    if opponent_name in player_roles: del player_roles[opponent_name]

                if waiting_player == current_user:
                    waiting_player = None
                print(f"User '{current_user}' disconnected.")
        conn.close()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Dòng này giúp tái sử dụng địa chỉ ngay, hữu ích khi bạn tắt/mở server liên tục
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Server is listening on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\nServer is shutting down...")
    finally:
        # Khối này luôn được thực thi, đảm bảo socket được đóng
        server_socket.close()
        print("Server has been closed.")

if __name__ == "__main__":
    main()