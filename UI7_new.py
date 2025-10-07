import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
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
            self.result_login.setText("⚠️ Vui lòng nhập đủ thông tin.")
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
                self.result_login.setText("❌ Sai tên đăng nhập hoặc mật khẩu.")
                s.close()
        except Exception as e:
            self.result_login.setText(f"⚠️ Không kết nối server ({e})")


    # ---- ĐĂNG KÝ ----
    def try_register(self):
        username = self.user_reg.text().strip()
        password = self.pass_reg.text().strip()
        if not username or not password:
            self.result_reg.setText("⚠️ Vui lòng nhập đủ thông tin.")
            return

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("127.0.0.1", 5000))
            s.send(f"/register {username} {password}".encode("utf-8"))
            resp = s.recv(1024).decode("utf-8")

            if resp == "/register_ok":
                self.result_reg.setStyleSheet("color:green;")
                self.result_reg.setText("✅ Đăng ký thành công! Hãy đăng nhập.")
                self.user_reg.clear()
                self.pass_reg.clear()
            else:
                self.result_reg.setText("❌ Tên tài khoản đã tồn tại.")
            s.close()
        except Exception as e:
            self.result_reg.setText(f"⚠️ Không thể kết nối ({e})")

# ---------------------- CLASS POPUP CHAT ----------------------
class ChatWindow(QtWidgets.QWidget):
    new_message_signal = QtCore.pyqtSignal(str)
    closed_signal = QtCore.pyqtSignal(str)

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
        layout.addWidget(self.chat_area)

        # ------- Ô nhập tin nhắn + nút Gửi -------
        input_layout = QtWidgets.QHBoxLayout()
        self.input_box = QtWidgets.QLineEdit(self)
        self.input_box.setPlaceholderText("Nhập tin nhắn...")
        self.input_box.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_box, 4)

        send_btn = QtWidgets.QPushButton("Gửi")
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn, 1)
        layout.addLayout(input_layout)

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

    def closeEvent(self, event):
        """Xử lý khi đóng cửa sổ chat riêng"""
        try:
            self.closed_signal.emit(self.to_user)
        except:
            pass
        event.accept() 

# ---------------------- CLASS MAIN WINDOW ----------------------
class MainWindow(QtWidgets.QWidget):
    new_message_signal = QtCore.pyqtSignal(str)
    user_list_signal = QtCore.pyqtSignal(list)
    open_pm_signal = QtCore.pyqtSignal(str, str)

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
        left_panel.addWidget(self.chat_area)

        # Hàng nhập tin nhắn + nút Gửi
        input_layout = QtWidgets.QHBoxLayout()
        self.input_box = QtWidgets.QLineEdit(self)
        self.input_box.setPlaceholderText("Nhập tin nhắn...")
        self.input_box.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_box, 4)

        send_btn = QtWidgets.QPushButton("Gửi")

        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn, 1)

        left_panel.addLayout(input_layout)
        layout.addLayout(left_panel, 3)

        # ---------- DANH SÁCH USER ONLINE + NÚT ĐĂNG XUẤT ----------
        right_panel = QtWidgets.QVBoxLayout()
        # --- Tiêu đề "Danh sách người đang online" ---
        title_label = QtWidgets.QLabel("👥 Danh sách người đang online")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #0078d7;
                margin-bottom: 6px;
            }
        """)
        right_panel.addWidget(title_label)

        # Danh sách user
        self.user_list = QtWidgets.QListWidget(self)
        self.user_list.itemDoubleClicked.connect(self.open_private_chat)
        right_panel.addWidget(self.user_list)

        # Nút Đăng xuất ở cuối danh sách
        logout_btn = QtWidgets.QPushButton("Đăng xuất")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4d4d;
                color: white;
                border-radius: 8px;
                padding: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff6666;
            }
            QPushButton:pressed {
                background-color: #e63946;
            }
        """)
        logout_btn.clicked.connect(self.logout)
        logout_container = QtWidgets.QHBoxLayout()
        logout_container.addStretch()
        logout_container.addWidget(logout_btn)
        logout_container.addStretch()

        right_panel.addLayout(logout_container)
        layout.addLayout(right_panel, 1)

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
            if not user:
                continue

            display_name = f"{user} (tôi)" if user == self.nickname else user
            item = QtWidgets.QListWidgetItem(f"  {display_name}")

            # Tạo icon tròn xanh lá
            pixmap = QtGui.QPixmap(14, 14)
            pixmap.fill(Qt.transparent)
            painter = QtGui.QPainter(pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setBrush(QtGui.QColor("#3CB371"))
            painter.setPen(QtGui.QPen(QtGui.QColor("#2E8B57")))
            painter.drawEllipse(1, 1, 12, 12)
            painter.end()

            item.setIcon(QtGui.QIcon(pixmap))
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

                # Không hiển thị chuỗi chứa /users trên UI
                if "/users " in msg:
                    main_part, user_part = msg.split("/users ", 1)
                    msg = main_part.strip()
                    users = user_part.split(",")
                    self.user_list_signal.emit(users)
                    if msg:
                        self.new_message_signal.emit(msg)
                    continue

                # Hiện danh sách user 
                if msg.startswith("/users "):
                    users = msg.replace("/users ", "").split(",")
                    self.user_list_signal.emit(users)
                    continue

                # Tin nhắn riêng tư
                # Tin nhắn lỗi khi gửi PM tới user không tồn tại
                if msg.startswith("/pm_error "):
                    try:
                        _, to_user, content = msg.split(" ", 2)
                        if to_user not in self.private_chats:
                            # Mở popup mới nếu chưa có
                            self.private_chats[to_user] = ChatWindow(self.nickname, to_user, self.client_socket)
                            self.private_chats[to_user].closed_signal.connect(self.remove_chat)
                            self.private_chats[to_user].show()

                        # Hiển thị lỗi trong popup chat tương ứng
                        error_html = (
                            f"<div style='color:red; font-size:12px;'>SERVER: {content}</div>"
                        )
                        self.private_chats[to_user].new_message(error_html)
                    except Exception as e:
                        print("Lỗi xử lý /pm_error:", e)
                    continue

                if msg.startswith("[PM từ"):
                    try:
                        sender = msg.split("[PM từ ", 1)[1].split("]:", 1)[0].strip()
                        # In đậm tên người gửi trong tin nhắn riêng
                        msg = msg.replace(f"[PM từ {sender}]:", f"<b>[PM từ {sender}]</b>:")
                    except Exception:
                        sender = "Unknown"
                    # Gửi tín hiệu mở popup
                    self.open_pm_signal.emit(sender, msg)
                    continue

                    # Định dạng thông báo hệ thống
                if msg.startswith("SERVER:"):
                    msg_text = msg.replace("SERVER:", "").strip()
                    # Gộp chung xử lý hệ thống
                    self.new_message_signal.emit(f"<i style='color:gray;'>{msg_text}</i>")
                    continue

                # Tin nhắn chung — in đậm tên người gửi nếu có dạng "tên: nội_dung"
                if ":" in msg and not msg.startswith("SERVER"):
                    parts = msg.split(":", 1)
                    sender = parts[0].strip()
                    content = parts[1].strip()
                    msg = f"<b>{sender}:</b> {content}"
                self.new_message_signal.emit(msg)

            except Exception as e:
                print("Lỗi khi nhận tin:", e)
                break


    # --------- XỬ LÝ HIỂN THỊ POPUP PM ---------
    def handle_private_message(self, sender, msg):
        if sender not in self.private_chats:
            self.private_chats[sender] = ChatWindow(self.nickname, sender, self.client_socket)
            self.private_chats[sender].closed_signal.connect(self.remove_chat)
            self.private_chats[sender].show()
        self.private_chats[sender].new_message(msg)
        self.private_chats[sender].raise_()
        self.private_chats[sender].activateWindow()

    # --------- MỞ CỬA SỔ CHAT RIÊNG ---------
    def open_private_chat(self, item):
        to_user = item.text().split(" (tôi)")[0].strip() 
        if to_user == self.nickname:
            return
        if to_user not in self.private_chats:
            self.private_chats[to_user] = ChatWindow(self.nickname, to_user, self.client_socket)
            self.private_chats[to_user].closed_signal.connect(self.remove_chat)
            self.private_chats[to_user].show()
        else:
            self.private_chats[to_user].raise_()
            self.private_chats[to_user].activateWindow()

    # --------- XÓA CỬA SỔ ĐÃ ĐÓNG ---------
    def remove_chat(self, to_user):
        if to_user in self.private_chats:
            del self.private_chats[to_user]

    # --------- ĐĂNG XUẤT ---------
    def logout(self):
        reply = QtWidgets.QMessageBox.question(
            self,
            "Đăng xuất",
            "Bạn có chắc muốn đăng xuất?",
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel,
            QtWidgets.QMessageBox.Cancel
        )

        if reply == QtWidgets.QMessageBox.Ok:
            # Đóng tất cả popup chat riêng
            for chat in list(self.private_chats.values()):
                chat.close()
            self.private_chats.clear()

            try:
                self.client_socket.send(b"/logout")
                self.client_socket.close()
            except:
                pass

            QtWidgets.QApplication.quit()
        else:
            # Người dùng chọn Cancel -> đóng popup, tiếp tục chat
            return

    def closeEvent(self, event):
        """Đóng tất cả popup chat riêng khi đóng cửa sổ chính"""
        try:
            # Đóng tất cả popup chat riêng
            for chat in list(self.private_chats.values()):
                chat.close()
            self.private_chats.clear()

            # Gửi lệnh logout về server
            self.client_socket.send(b"/logout")
            self.client_socket.close()
        except:
            pass

        event.accept()   

# ---------------------- MAIN ----------------------
def main():
    app = QtWidgets.QApplication(sys.argv)

    # ---------------------- GLOBAL STYLE ----------------------
    app.setStyleSheet("""
        QWidget {
            background-color: #fafafa;
            font-family: Segoe UI, sans-serif;
            font-size: 14px;
        }
        QLineEdit {
            border: 2px solid #0078d7;
            border-radius: 6px;
            padding: 6px;
            background: white;
        }
        QLineEdit:focus {
            border-color: #005999;
            background: #f0f8ff;
        }
        QPushButton {
            background-color: #0078d7;
            color: white;
            border-radius: 8px;
            padding: 6px 10px;
            font-weight: 600;
        }
        QPushButton:hover { background-color: #339cff; }
        QPushButton:pressed { background-color: #005999; }
        QTextEdit {
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                        stop:0 #f5f7fa, stop:1 #c3cfe2);
            border-radius: 10px;
            padding: 6px;
        }
        QListWidget {
            background-color: #f0f0f0;
            border-radius: 10px;
            padding: 4px;
        }
        QListWidget::item:selected {
            background: #aee1f9;
            color: black;
        }
    """)

    auth = AuthWindow()
    if auth.exec_() == QtWidgets.QDialog.Accepted:
        nickname = auth.nickname
        client_socket = auth.client_socket
        window = MainWindow(nickname, client_socket)
        window.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
