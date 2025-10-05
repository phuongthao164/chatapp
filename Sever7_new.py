import socket
import threading
import json
import os

HOST = "0.0.0.0"
PORT = 5000
DATA_FILE = "users.json"

clients = {}  # nickname -> socket
accounts = {}  # username -> password


# ---------------------- HÀM XỬ LÝ TÀI KHOẢN ----------------------
def load_accounts():
    """Đọc file users.json (nếu tồn tại)"""
    global accounts
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                accounts = json.load(f)
            print(f"📂 Đã tải {len(accounts)} tài khoản từ {DATA_FILE}")
        except Exception as e:
            print(f"⚠️ Lỗi khi đọc file {DATA_FILE}: {e}")
            accounts = {}
    else:
        accounts = {}
        print("📄 Chưa có file users.json — sẽ tạo mới khi đăng ký đầu tiên.")


def save_accounts():
    """Ghi danh sách tài khoản ra file"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(accounts, f, indent=4, ensure_ascii=False)
        print(f"💾 Đã lưu {len(accounts)} tài khoản vào {DATA_FILE}")
    except Exception as e:
        print(f"⚠️ Lỗi khi lưu file {DATA_FILE}: {e}")

        
# ---------------------- CHAT CHUNG ----------------------
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

            if msg.strip() == "/logout":
                break

            if msg.startswith("/pm "):
                parts = msg.split(" ", 2)
                if len(parts) >= 3:
                    to_user = parts[1].strip()   
                    content = parts[2].strip()

                    # Gửi tin riêng
                    if to_user in clients:
                        clients[to_user].send((f"[PM từ {nickname}]: {content}\n").encode("utf-8"))
                    else:
                    # Báo lại cho người gửi nếu không tìm thấy người nhận
                        client.send((f"SERVER: Không tìm thấy người dùng '{to_user}'\n").encode("utf-8"))
            else:
                broadcast(f"{nickname}: {msg}", client)

    except Exception as e:
        print(f"⚠️ Lỗi xử lý {nickname}: {e}")

    finally:
        # Xóa client khỏi danh sách nếu còn tồn tại
        if nickname in clients:
            try:
                del clients[nickname]
            except KeyError:
                pass

        try:
            client.close()
        except:
            pass
        
        print(f"❌ {nickname} đã thoát")
        broadcast(f"SERVER: {nickname} đã thoát")
        update_online_list()

def update_online_list():
    user_list = "/users " + ",".join(clients.keys())
    for client in clients.values():
        try:
            client.send(user_list.encode("utf-8"))
        except:
            pass

# ---------------------- XỬ LÝ LOGIN / REGISTER ----------------------
def main():
    load_accounts()  # ← đọc danh sách user khi khởi động

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"🚀 Server đang chạy tại {HOST}:{PORT} ...")

    while True:
        client, addr = server.accept()
        print(f"🔗 Kết nối mới từ {addr}")

        try:
            data = client.recv(1024).decode("utf-8")
            if not data:
                client.close()
                continue

            # ---- ĐĂNG KÝ ----
            if data.startswith("/register "):
                _, username, password = data.split(" ", 2)
                if username in accounts:
                    client.send(b"/register_fail")
                    client.close()
                    continue

                accounts[username] = password
                save_accounts()  # ← lưu lại file sau khi đăng ký
                client.send(b"/register_ok")
                print(f"🆕 Đăng ký mới: {username}")
                client.close()
                continue

            # ---- ĐĂNG NHẬP ----
            if data.startswith("/login "):
                _, username, password = data.split(" ", 2)
                if username in accounts and accounts[username] == password:
                    client.send(b"/login_ok")
                    threading.Thread(target=handle_client, args=(client, username), daemon=True).start()
                else:
                    client.send(b"/login_fail")
                    client.close()
                    continue

            else:
                client.close()

        except Exception as e:
            print("⚠️ Lỗi khi nhận login/register:", e)
            client.close()

if __name__ == "__main__":
    main()
