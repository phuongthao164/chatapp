import sys
import socket
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QInputDialog

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
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"LAN Chat - {nickname}")
        self.setGeometry(200, 100, 600, 400)

        layout = QVBoxLayout()

        self.chat_box = QTextEdit()
        self.chat_box.setReadOnly(True)
        layout.addWidget(self.chat_box)

        input_layout = QHBoxLayout()
        self.msg_input = QLineEdit()
        self.send_btn = QPushButton("Gửi")
        self.send_btn.clicked.connect(self.send_msg)
        input_layout.addWidget(self.msg_input)
        input_layout.addWidget(self.send_btn)

        layout.addLayout(input_layout)
        self.setLayout(layout)

        threading.Thread(target=self.receive, daemon=True).start()

    def receive(self):
        while True:
            try:
                msg = client.recv(1024).decode("utf-8")
                if msg == "NICK":
                    client.send(nickname.encode("utf-8"))
                else:
                    self.chat_box.append(msg)
            except:
                client.close()
                break

    def send_msg(self):
        msg = f"{nickname}: {self.msg_input.text()}"
        client.send(msg.encode("utf-8"))
        self.msg_input.clear()

if __name__ == "__main__":
    win = ChatApp()
    win.show()
    sys.exit(app.exec_())