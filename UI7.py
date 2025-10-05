import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import sys
import socket
import threading
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt


# ---------------------- CLASS POPUP CHAT ----------------------
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

        # Khu vực hiển thị chat
        self.chat_area = QtWidgets.QTextEdit(self)
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("""
            QTextEdit {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                stop:0 #f5f7fa, stop:1 #c3cfe2);
                border-radius: 10px;
                padding: 6px;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.chat_area)

        # Ô nhập tin nhắn
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

        # Signal cập nhật tin nhắn
        self.new_message_signal.connect(self.chat_area.append)

    def send_message(self):
        msg = self.input_box.text().strip()
        if msg:
            self.client_socket.send(f"/pm {self.to_user} {msg}".encode("utf-8"))
            self.chat_area.append(f"<b>Bạn → {self.to_user}:</b> {msg}")
            self.input_box.clear()

    def new_message(self, msg):
        self.new_message_signal.emit(msg)


# ---------------------- CLASS MAIN WINDOW ----------------------
class MainWindow(QtWidgets.QWidget):
    new_message_signal = QtCore.pyqtSignal(str)
    user_list_signal = QtCore.pyqtSignal(list)
    open_pm_signal = QtCore.pyqtSignal(str, str)  # sender, msg

    def __init__(self, nickname, client_socket):
        super().__init__()
        self.nickname = nickname
        self.client_socket = client_socket
        self.private_chats = {}

        self.setWindowTitle(f"Trò chuyện cùng - {nickname}")
        self.resize(700, 400)

        layout = QtWidgets.QHBoxLayout(self)

        # ---------- KHU VỰC CHAT CHUNG ----------
        left_panel = QtWidgets.QVBoxLayout()

        self.chat_area = QtWidgets.QTextEdit(self)
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("""
            QTextEdit {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                stop:0 #d9a7c7, stop:1 #fffcdc);
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

        # ---------- DANH SÁCH USER ONLINE ----------
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

        # ---------- KẾT NỐI SIGNAL ----------
        self.new_message_signal.connect(self.chat_area.append)
        self.user_list_signal.connect(self.update_user_list)
        self.open_pm_signal.connect(self.handle_private_message)

        # Thread nhận tin nhắn từ server
        threading.Thread(target=self.receive_messages, daemon=True).start()

    # --------- CẬP NHẬT DANH SÁCH USER ONLINE ---------
    def update_user_list(self, users):
        self.user_list.clear()
        for user in users:
            if user:
                item = QtWidgets.QListWidgetItem(user)
                # Biểu tượng chấm xanh online
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

    # --------- GỬI TIN NHẮN CHUNG ---------
    def send_message(self):
        msg = self.input_box.text().strip()
        if msg:
            self.client_socket.send(msg.encode("utf-8"))
            self.chat_area.append(f"<b>Bạn:</b> {msg}")
            self.input_box.clear()

    # --------- NHẬN TIN TỪ SERVER ---------
    def receive_messages(self):
        while True:
            try:
                msg = self.client_socket.recv(1024).decode("utf-8")
                if not msg:
                    break

                # Nếu chuỗi chứa /users
                if "/users " in msg:
                    main_part, user_part = msg.split("/users ", 1)
                    msg = main_part.strip()
                    users = user_part.split(",")
                    self.user_list_signal.emit(users)
                    if msg:
                        self.new_message_signal.emit(msg)
                    continue

                # Nếu chỉ là danh sách user
                if msg.startswith("/users "):
                    users = msg.replace("/users ", "").split(",")
                    self.user_list_signal.emit(users)
                    continue

                # Tin nhắn riêng tư
                if msg.startswith("[PM từ"):
                    try:
                        sender = msg.split("[PM từ ", 1)[1].split("]:", 1)[0].strip()
                    except Exception:
                        sender = "Unknown"
                    # Emit signal để UI chính mở popup
                    self.open_pm_signal.emit(sender, msg)
                    continue

                # Tin nhắn chung
                self.new_message_signal.emit(msg)

            except Exception as e:
                print("Lỗi khi nhận tin:", e)
                break

    # --------- XỬ LÝ HIỂN THỊ POPUP PM ---------
    def handle_private_message(self, sender, msg):
        if sender not in self.private_chats:
            self.private_chats[sender] = ChatWindow(self.nickname, sender, self.client_socket)
            self.private_chats[sender].show()
        self.private_chats[sender].new_message(msg)
        # Làm nổi bật cửa sổ khi có tin nhắn mới
        self.private_chats[sender].raise_()
        self.private_chats[sender].activateWindow()

    # --------- MỞ CỬA SỔ CHAT RIÊNG ---------
    def open_private_chat(self, item):
        to_user = item.text()
        if to_user == self.nickname:
            return
        if to_user not in self.private_chats:
            self.private_chats[to_user] = ChatWindow(self.nickname, to_user, self.client_socket)
            self.private_chats[to_user].show()


# ---------------------- MAIN ----------------------
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
