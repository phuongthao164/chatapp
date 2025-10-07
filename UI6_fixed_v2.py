
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import sys
import socket
import threading
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt


class ChatWindow(QtWidgets.QWidget):
    new_message_signal = QtCore.pyqtSignal(str)

    def __init__(self, nickname, to_user, client_socket):
        super().__init__()
        self.nickname = nickname
        self.to_user = to_user
        self.client_socket = client_socket

        self.setWindowTitle(f"Private chat với {to_user}")
        self.resize(400, 300)

        layout = QtWidgets.QVBoxLayout(self)

        self.chat_area = QtWidgets.QTextEdit(self)
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("""
            QTextEdit {
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f5f7fa, stop:1 #c3cfe2
                );
                border-radius: 10px;
                padding: 6px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.chat_area)

        self.input_box = QtWidgets.QLineEdit(self)
        self.input_box.setPlaceholderText("Nhập tin nhắn và nhấn Enter...")
        self.input_box.returnPressed.connect(self.send_message)
        self.input_box.setStyleSheet("""
            QLineEdit {
                border: 2px solid #6a11cb;
                border-radius: 8px;
                padding: 6px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.input_box)

        self.new_message_signal.connect(self.chat_area.append)

    def send_message(self):
        msg = self.input_box.text().strip()
        if msg:
            self.client_socket.send(f"/pm {self.to_user} {msg}".encode("utf-8"))
            self.chat_area.append(f"<b>Bạn → {self.to_user}:</b> {msg}")
            self.input_box.clear()

    def new_message(self, msg):
        self.new_message_signal.emit(msg)


class MainWindow(QtWidgets.QWidget):
    new_message_signal = QtCore.pyqtSignal(str)
    user_list_signal = QtCore.pyqtSignal(list)

    def __init__(self, nickname, client_socket):
        super().__init__()
        self.nickname = nickname
        self.client_socket = client_socket
        self.private_chats = {}

        self.setWindowTitle(f"Trò chuyện cùng - {nickname}")
        self.resize(700, 400)

        layout = QtWidgets.QHBoxLayout(self)

        left_panel = QtWidgets.QVBoxLayout()

        self.chat_area = QtWidgets.QTextEdit(self)
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("""
            QTextEdit {
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 #d9a7c7, stop:1 #fffcdc
                );
                border-radius: 10px;
                padding: 8px;
                font-size: 14px;
            }
        """)
        left_panel.addWidget(self.chat_area)

        self.input_box = QtWidgets.QLineEdit(self)
        self.input_box.setPlaceholderText("Nhập tin nhắn và nhấn Enter...")
        self.input_box.returnPressed.connect(self.send_message)
        self.input_box.setStyleSheet("""
            QLineEdit {
                border: 2px solid #2575fc;
                border-radius: 8px;
                padding: 6px;
                font-size: 14px;
            }
        """)
        left_panel.addWidget(self.input_box)

        layout.addLayout(left_panel, 3)

        self.user_list = QtWidgets.QListWidget(self)
        self.user_list.itemDoubleClicked.connect(self.open_private_chat)
        self.user_list.setStyleSheet("""
            QListWidget {
                background-color: #f0f0f0;
                border-radius: 10px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 6px;
            }
            QListWidget::item:selected {
                background: #6a11cb;
                color: black;
            }
        """)
        layout.addWidget(self.user_list, 1)

        self.new_message_signal.connect(self.chat_area.append)
        self.user_list_signal.connect(self.update_user_list)

        threading.Thread(target=self.receive_messages, daemon=True).start()

    def update_user_list(self, users):
        self.user_list.clear()
        for user in users:
            if user:
                item = QtWidgets.QListWidgetItem(user)
                pixmap = QtGui.QPixmap(12, 12)
                pixmap.fill(Qt.transparent)
                painter = QtGui.QPainter(pixmap)
                painter.setBrush(Qt.green)
                painter.setPen(Qt.green)
                painter.drawEllipse(0, 0, 12, 12)
                painter.end()
                icon = QtGui.QIcon(pixmap)
                item.setIcon(icon)
                self.user_list.addItem(item)

    def send_message(self):
        msg = self.input_box.text().strip()
        if msg:
            self.client_socket.send(msg.encode("utf-8"))
            self.chat_area.append(f"<b>Bạn:</b> {msg}")
            self.input_box.clear()

    def receive_messages(self):
        while True:
            try:
                msg = self.client_socket.recv(1024).decode("utf-8")
                if not msg:
                    break

                # Trường hợp /users bị dính sau thông báo SERVER:
                if "/users " in msg:
                    main_part, user_part = msg.split("/users ", 1)
                    msg = main_part.strip()

                    users = user_part.split(",")
                    self.user_list_signal.emit(users)

                    if msg:
                        self.new_message_signal.emit(msg)
                    continue

                # Nếu là gói chỉ chứa /users
                if msg.startswith("/users "):
                    users = msg.replace("/users ", "").split(",")
                    self.user_list_signal.emit(users)
                    continue

                # Tin nhắn riêng (PM)
                if msg.startswith("[PM từ"):
                    sender = msg.split(" ")[2][:-2]
                    if sender not in self.private_chats:
                        self.private_chats[sender] = ChatWindow(self.nickname, sender, self.client_socket)
                        self.private_chats[sender].show()
                    self.private_chats[sender].new_message(msg)
                    continue

                # Tin nhắn thông thường
                self.new_message_signal.emit(msg)

            except Exception as e:
                print("Lỗi khi nhận tin:", e)
                break

    def open_private_chat(self, item):
        to_user = item.text()
        if to_user == self.nickname:
            return
        if to_user not in self.private_chats:
            self.private_chats[to_user] = ChatWindow(self.nickname, to_user, self.client_socket)
            self.private_chats[to_user].show()


def main():
    app = QtWidgets.QApplication(sys.argv)

    nickname, ok = QtWidgets.QInputDialog.getText(None, "Đăng nhập", "Nhập nickname của bạn:")
    if not ok or not nickname:
        return

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("127.0.0.1", 5000))
    client_socket.send(nickname.encode("utf-8"))

    window = MainWindow(nickname, client_socket)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
