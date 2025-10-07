import sys
import socket
import threading
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt


# ---------------------- LOGIN & REGISTER WINDOW ----------------------
class AuthWindow(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Đăng nhập / Đăng ký")
        self.resize(320, 200)
        self.client_socket = None

        tabs = QtWidgets.QTabWidget()
        self.login_tab = self._create_login_tab()
        self.register_tab = self._create_register_tab()
        tabs.addTab(self.login_tab, "Đăng nhập")
        tabs.addTab(self.register_tab, "Đăng ký")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(tabs)

    # ---- TAB ĐĂNG NHẬP ----
    def _create_login_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)

        self.user_login = QtWidgets.QLineEdit()
        self.user_login.setPlaceholderText("Tên đăng nhập")
        layout.addWidget(self.user_login)

        self.pass_login = QtWidgets.QLineEdit()
        self.pass_login.setPlaceholderText("Mật khẩu")
        self.pass_login.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addWidget(self.pass_login)

        btn = QtWidgets.QPushButton("Đăng nhập")
        btn.clicked.connect(self.try_login)
        layout.addWidget(btn)

        self.result_login = QtWidgets.QLabel("")
        self.result_login.setStyleSheet("color:red;")
        layout.addWidget(self.result_login)
        return tab

    # ---- TAB ĐĂNG KÝ ----
    def _create_register_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)

        self.user_reg = QtWidgets.QLineEdit()
        self.user_reg.setPlaceholderText("Tên đăng nhập mới")
        layout.addWidget(self.user_reg)

        self.pass_reg = QtWidgets.QLineEdit()
        self.pass_reg.setPlaceholderText("Mật khẩu")
        self.pass_reg.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addWidget(self.pass_reg)

        btn = QtWidgets.QPushButton("Đăng ký")
        btn.clicked.connect(self.try_register)
        layout.addWidget(btn)

        self.result_reg = QtWidgets.QLabel("")
        self.result_reg.setStyleSheet("color:red;")
        layout.addWidget(self.result_reg)
        return tab

    # ---- ĐĂNG NHẬP ----
    def try_login(self):
        username = self.user_login.text().strip()
        password = self.pass_login.text().strip()
        if not username or not password:
            self.result_login.setText("⚠️ Nhập đủ thông tin.")
            return

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("127.0.0.1", 5000))
            s.send(f"/login {username} {password}".encode("utf-8"))
            resp = s.recv(1024).decode("utf-8")

            if resp == "/login_ok":
                self.client_socket = s
                self.nickname = username
                self.accept()
            else:
                self.result_login.setText("❌ Sai tài khoản hoặc mật khẩu.")
                s.close()
        except Exception as e:
            self.result_login.setText(f"⚠️ Không kết nối server ({e})")

    # ---- ĐĂNG KÝ ----
    def try_register(self):
        username = self.user_reg.text().strip()
        password = self.pass_reg.text().strip()
        if not username or not password:
            self.result_reg.setText("⚠️ Nhập đủ thông tin.")
            return

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("127.0.0.1", 5000))
            s.send(f"/register {username} {password}".encode("utf-8"))
            resp = s.recv(1024).decode("utf-8")

            if resp == "/register_ok":
                self.result_reg.setStyleSheet("color:green;")
                self.result_reg.setText("✅ Đăng ký thành công! Hãy đăng nhập.")
            else:
                self.result_reg.setText("❌ Tên tài khoản đã tồn tại.")
            s.close()
        except Exception as e:
            self.result_reg.setText(f"⚠️ Không thể kết nối ({e})")


# ---------------------- PRIVATE CHAT WINDOW ----------------------
class ChatWindow(QtWidgets.QWidget):
    closed_signal = QtCore.pyqtSignal(str)
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
        layout.addWidget(self.chat_area)

        self.input_box = QtWidgets.QLineEdit(self)
        self.input_box.setPlaceholderText("Nhập tin nhắn và nhấn Enter...")
        self.input_box.returnPressed.connect(self.send_message)
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

    def closeEvent(self, event):
        self.closed_signal.emit(self.to_user)
        super().closeEvent(event)


# ---------------------- MAIN CHAT WINDOW ----------------------
class MainWindow(QtWidgets.QWidget):
    new_message_signal = QtCore.pyqtSignal(str)
    user_list_signal = QtCore.pyqtSignal(list)
    open_pm_signal = QtCore.pyqtSignal(str, str)

    def __init__(self, nickname, client_socket):
        super().__init__()
        self.nickname = nickname
        self.client_socket = client_socket
        self.private_chats = {}

        self.setWindowTitle(f"Phòng chat - {nickname}")
        self.resize(700, 400)

        layout = QtWidgets.QHBoxLayout(self)
        left_panel = QtWidgets.QVBoxLayout()

        self.chat_area = QtWidgets.QTextEdit(self)
        self.chat_area.setReadOnly(True)
        left_panel.addWidget(self.chat_area)

        self.input_box = QtWidgets.QLineEdit(self)
        self.input_box.setPlaceholderText("Nhập tin nhắn và nhấn Enter...")
        self.input_box.returnPressed.connect(self.send_message)
        left_panel.addWidget(self.input_box)

        logout_btn = QtWidgets.QPushButton("Đăng xuất")
        logout_btn.clicked.connect(self.logout)
        left_panel.addWidget(logout_btn)

        layout.addLayout(left_panel, 3)

        self.user_list = QtWidgets.QListWidget(self)
        self.user_list.itemDoubleClicked.connect(self.open_private_chat)
        layout.addWidget(self.user_list, 1)

        self.new_message_signal.connect(self.chat_area.append)
        self.user_list_signal.connect(self.update_user_list)
        self.open_pm_signal.connect(self.handle_private_message)

        threading.Thread(target=self.receive_messages, daemon=True).start()

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
                if msg.startswith("/users "):
                    users = msg.replace("/users ", "").split(",")
                    self.user_list_signal.emit(users)
                    continue
                if msg.startswith("[PM từ"):
                    sender = msg.split("[PM từ ", 1)[1].split("]:", 1)[0].strip()
                    self.open_pm_signal.emit(sender, msg)
                    continue
                self.new_message_signal.emit(msg)
            except:
                break

    def update_user_list(self, users):
        self.user_list.clear()
        for user in users:
            if user:
                self.user_list.addItem(user)

    def handle_private_message(self, sender, msg):
        if sender not in self.private_chats:
            chat = ChatWindow(self.nickname, sender, self.client_socket)
            chat.closed_signal.connect(self.remove_chat)
            self.private_chats[sender] = chat
            chat.show()
        self.private_chats[sender].new_message(msg)
        self.private_chats[sender].raise_()
        self.private_chats[sender].activateWindow()

    def open_private_chat(self, item):
        to_user = item.text()
        if to_user == self.nickname:
            return
        if to_user not in self.private_chats:
            chat = ChatWindow(self.nickname, to_user, self.client_socket)
            chat.closed_signal.connect(self.remove_chat)
            self.private_chats[to_user] = chat
            chat.show()

    def remove_chat(self, to_user):
        if to_user in self.private_chats:
            del self.private_chats[to_user]

    def logout(self):
        try:
            self.client_socket.send(b"/logout")
            self.client_socket.close()
        except:
            pass
        QtWidgets.QMessageBox.information(self, "Đăng xuất", "Bạn đã đăng xuất!")
        QtWidgets.QApplication.quit()


# ---------------------- MAIN ----------------------
def main():
    app = QtWidgets.QApplication(sys.argv)
    auth = AuthWindow()
    if auth.exec_() == QtWidgets.QDialog.Accepted:
        nickname = auth.nickname
        client_socket = auth.client_socket
        window = MainWindow(nickname, client_socket)
        window.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
