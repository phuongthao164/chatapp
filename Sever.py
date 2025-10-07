import socket
import threading

HOST = "0.0.0.0"
PORT = 5000

clients = []
nicknames = []

# Gửi tin nhắn tới tất cả client
def broadcast(message, _client=None):
    for client in clients:
        if client != _client:
            try:
                client.send(message)
            except:
                client.close()
                if client in clients:
                    clients.remove(client)

# Gửi tin nhắn riêng tư
def private_message(sender, target_nick, message):
    if target_nick in nicknames:
        idx = nicknames.index(target_nick)
        target_client = clients[idx]
        try:
            target_client.send(f"[PM từ {sender}]: {message}".encode("utf-8"))
        except:
            target_client.close()
            clients.remove(target_client)
            nicknames.remove(target_nick)
    else:
        sender_idx = nicknames.index(sender)
        clients[sender_idx].send(f"Không tìm thấy user {target_nick}".encode("utf-8"))

# Xử lý tin nhắn từ client
def handle_client(client):
    while True:
        try:
            msg = client.recv(1024).decode("utf-8")
            if msg.startswith("/users"):  # danh sách online
                user_list = ", ".join(nicknames)
                client.send(f"Đang online: {user_list}".encode("utf-8"))
            elif msg.startswith("/pm"):  # tin nhắn riêng
                parts = msg.split(" ", 2)
                if len(parts) >= 3:
                    target = parts[1]
                    sender = nicknames[clients.index(client)]
                    message = parts[2]
                    private_message(sender, target, message)
            else:
                broadcast(msg.encode("utf-8"), client)
        except:
            if client in clients:
                idx = clients.index(client)
                nickname = nicknames[idx]
                clients.remove(client)
                nicknames.remove(nickname)
                broadcast(f"{nickname} rời khỏi phòng!\n".encode("utf-8"))
                client.close()
            break

# Chấp nhận kết nối mới
def receive():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"Server đang chạy tại {HOST}:{PORT} ...")

    while True:
        client, addr = server.accept()
        print(f"Kết nối từ {addr}")

        client.send("NICK".encode("utf-8"))
        nickname = client.recv(1024).decode("utf-8")
        nicknames.append(nickname)
        clients.append(client)

        print(f"Nickname: {nickname}")
        broadcast(f"{nickname} đã tham gia!\n".encode("utf-8"))
        client.send("Kết nối thành công đến server!\n".encode("utf-8"))

        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()
if __name__ == "__main__":
    receive()
    #353