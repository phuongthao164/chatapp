import socket
import threading

HOST = "0.0.0.0"
PORT = 5000

clients = {}  # nickname -> socket

# Gửi tin nhắn cho tất cả client (broadcast)
def broadcast(message, _client=None):
    for client in clients.values():
        if client != _client:
            try:
                client.send((message + "\n").encode("utf-8"))
            except:
                pass

def handle_client(client, nickname):
    clients[nickname] = client
    print(f"✅ {nickname} đã kết nối")

    # Thông báo user online
    broadcast(f"SERVER: {nickname} đã tham gia phòng chat\n")
    update_online_list()

    try:
        while True:
            msg = client.recv(1024).decode("utf-8")
            if not msg:
                break

            # if msg.startswith("/pm "):
            #     parts = msg.split(" ", 2)
            #     if len(parts) >= 3:
            #         to_user, content = parts[1], parts[2]
            #         if to_user in clients:
            #             clients[to_user].send(f"[PM từ {nickname}]: {content}".encode("utf-8"))
            if msg.startswith("/pm "):
                parts = msg.split(" ", 2)
                if len(parts) >= 3:
                    to_user = parts[1].strip()   # loại bỏ khoảng trắng thừa
                    content = parts[2].strip()

                     # In log để debug
                    print(f"📩 Tin nhắn riêng từ {nickname} -> {to_user}: {content}")
                    print("Danh sách clients hiện có:", list(clients.keys()))

                    # Gửi tin riêng
                    if to_user in clients:
                        clients[to_user].send((f"[PM từ {nickname}]: {content}\n").encode("utf-8"))
                    else:
                    # Báo lại cho người gửi nếu không tìm thấy người nhận
                        client.send((f"SERVER: Không tìm thấy người dùng '{to_user}'\n").encode("utf-8"))
            else:
                broadcast(f"{nickname}: {msg}", client)
    except:
        pass
    finally:
        client.close()
        del clients[nickname]
        print(f"❌ {nickname} đã rời đi")
        broadcast(f"SERVER: {nickname} đã thoát")
        update_online_list()

def update_online_list():
    user_list = "/users " + ",".join(clients.keys())
    for client in clients.values():
        try:
            client.send(user_list.encode("utf-8"))
        except:
            pass

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"🚀 Server đang chạy tại {HOST}:{PORT} ...")

    while True:
        client, addr = server.accept()
        nickname = client.recv(1024).decode("utf-8")
        threading.Thread(target=handle_client, args=(client, nickname), daemon=True).start()

if __name__ == "__main__":
    main()
