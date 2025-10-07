import sys
import socket
import threading
from PyQt5 import QtCore, QtGui, QtWidgets


class ChatClient(QtWidgets.QMainWindow):
    def __init__(self, host="127.0.0.1", port=5000, nickname="User"):
        super().__init__()
        self.host = host
        self.port = port
        self.nickname = nickname
        self.socket = None

        self.initUI()
        self.connect_to_server()

    def initUI(self):
        self.setWindowTitle(f"Chat App - {self.nickname}")
        self.resize(900, 600)

        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QtWidgets.QHBoxLayout(central_widget)

        # Sidebar bạn bè
        self.sidebar = QtWidgets.QListWidget()
        self.sidebar.setFixedWidth(200)
        main_layout.addWidget(self.sidebar)

        # Khu chat
        right_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(right_layout)

        # Header
        self.chatHeader = QtWidgets.QLabel(f"Đang chat với mọi người")
        self.chatHeader.setStyleSheet("font-weight: bold; font-size: 16px; padding: 5px;")
        right_layout.addWidget(self.chatHeader)

        # Khu hiển thị tin nhắn
        self.messageArea = QtWidgets.QTextEdit()
        self.messageArea.setReadOnly(True)
        self.messageArea.setStyleSheet("background-color: #e5ddd5; padding: 10px;")
        right_layout.addWidget(self.messageArea)

        # Nhập tin nhắn
        input_layout = QtWidgets.QHBoxLayout()
        self.messageInput = QtWidgets.QLineEdit()
        self.messageInput.setPlaceholderText("Nhập tin nhắn...")
        self.sendButton = QtWidgets.QPushButton("Gửi")
        self.sendButton.setStyleSheet("background-color:#0084ff; color:white; padding:5px; border-radius:5px;")

        input_layout.addWidget(self.messageInput)
        input_layout.addWidget(self.sendButton)
        right_layout.addLayout(input_layout)

        # Sự kiện gửi tin
        self.sendButton.clicked.connect(self.sendMessage)
        self.messageInput.returnPressed.connect(self.sendMessage)

    def connect_to_server(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))

            # Gửi nickname
            msg = self.socket.recv(1024).decode("utf-8")
            if msg == "NICK":
                self.socket.send(self.nickname.encode("utf-8"))

            # Thread nhận tin nhắn
            thread = threading.Thread(target=self.receive_messages)
            thread.daemon = True
            thread.start()
        except Exception as e:
            self.messageArea.append(f"❌ Không thể kết nối server: {e}")

    def receive_messages(self):
        while True:
            try:
                msg = self.socket.recv(1024).decode("utf-8")
                if msg.startswith("[CLIENTS]"):
                    users = msg.replace("[CLIENTS]", "").split(",")
                    self.sidebar.clear()
                    self.sidebar.addItems(users)
                else:
                    # Bong bóng màu trắng (tin nhắn từ người khác)
                    self.messageArea.insertHtml(
                        f'<div align="left" style="margin:5px;">'
                        f'<span style="background-color:#f1f0f0; color:black; padding:8px; border-radius:10px; max-width:60%; display:inline-block;">'
                        f'{msg}'
                        f'</span></div>'
                    )
                    self.messageArea.insertPlainText("\n")
            except:
                self.messageArea.append("⚠️ Mất kết nối với server.")
                self.socket.close()
                break
    def sendMessage(self):
        msg = self.messageInput.text()
        if msg.strip():
            try:
                self.socket.send(f"{self.nickname}: {msg}".encode("utf-8"))
            except:
                self.messageArea.append("⚠️ Không gửi được tin nhắn (mất kết nối).")
                return

            # Hiển thị bong bóng màu xanh (tin nhắn của mình)
            self.messageArea.insertHtml(
                f'<div align="right" style="margin:5px;">'
                f'<span style="background-color:#0084ff; color:white; padding:8px; border-radius:10px; max-width:60%; display:inline-block;">'
                f'{msg}'
                f'</span></div>'
            )
            self.messageArea.insertPlainText("\n")  # xuống dòng
            self.messageInput.clear()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    nickname, ok = QtWidgets.QInputDialog.getText(None, "Nickname", "Nhập nickname của bạn:")
    if ok and nickname.strip():
        window = ChatClient("127.0.0.1", 5000, nickname)
        window.show()
        sys.exit(app.exec_())
