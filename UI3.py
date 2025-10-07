import sys
import socket
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QInputDialog, QListWidget

HOST = "127.0.0.1"
PORT = 5000

# Hỏi nickname bằng popup
app = QApplication(sys.argv)
nickname, ok = QInputDialog.getText(None, "Nhập tên", "Nickname:")
if not ok or nickname.strip() == "":
    sys.exit()

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

class ChatApp(QWidget):
    def __init__(self, nickname):
        super().__init__()
        self.setWindowTitle(f"LAN Chat - {nickname}")
        self.setGeometry(200, 100, 800, 400)

        main_layout = QHBoxLayout(self)   # layout chính ngang

        # --- Sidebar trái: Danh sách user ---
        self.user_list = QListWidget()
        self.user_list.setFixedWidth(150)   # chiều rộng sidebar
        main_layout.addWidget(self.user_list)

        # --- Khu chat bên phải ---
        chat_layout = QVBoxLayout()

        self.chat_box = QTextEdit()
        self.chat_box.setReadOnly(True)
        chat_layout.addWidget(self.chat_box)

        input_layout = QHBoxLayout()
        self.msg_input = QLineEdit()
        self.send_btn = QPushButton("Gửi")
        self.send_btn.clicked.connect(self.send_msg)
        self.msg_input.returnPressed.connect(self.send_msg)

        input_layout.addWidget(self.msg_input)
        input_layout.addWidget(self.send_btn)
        chat_layout.addLayout(input_layout)

        # Gắn chat layout vào main layout
        main_layout.addLayout(chat_layout)

        # Thread nhận tin nhắn
        threading.Thread(target=self.receive, daemon=True).start()

    def receive(self):
        while True:
            try:
                msg = client.recv(1024).decode("utf-8")
                if msg == "NICK":
                    client.send(nickname.encode("utf-8"))
                elif msg.startswith("Đang online:"):
                    # Cập nhật danh sách user
                    users = msg.replace("Đang online:", "").strip().split(", ")
                    self.user_list.clear()
                    self.user_list.addItems(users)
                else:
                    self.chat_box.append(msg)
            except:
                client.close()
                break

    def send_msg(self):
        text = self.msg_input.text().strip()
        if not text:
            return

        # Nếu là lệnh (bắt đầu bằng "/")
        if text.startswith("/"):
            msg = text
        else:
            msg = f"{nickname}: {text}"

        client.send(msg.encode("utf-8"))
        self.msg_input.clear()


if __name__ == "__main__":
    win = ChatApp()
    win.show()
    sys.exit(app.exec_())