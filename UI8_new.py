# ui_demo.py
# PyQt5 modern chat UI demo with bubbles, hover, avatars, theme toggle
# Run: python ui_demo.py

import sys
from datetime import datetime
from PyQt5 import QtWidgets, QtGui, QtCore

PRIMARY = "#0078d7"
LIGHT_BG = "#fafafa"
CARD_BG = "#f7fbff"
BUBBLE_SELF = "#d4f0c0"
BUBBLE_OTHER = "#f0f0f0"
DARK_BG = "#1e1e1e"
DARK_CARD = "#2b2b2b"
DARK_TEXT = "#e6e6e6"

class Avatar:
    @staticmethod
    def create_pixmap(letter: str, size=36, bg="#34c759", fg="#ffffff"):
        pix = QtGui.QPixmap(size, size)
        pix.fill(QtCore.Qt.transparent)
        p = QtGui.QPainter(pix)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        brush = QtGui.QBrush(QtGui.QColor(bg))
        p.setBrush(brush)
        p.setPen(QtCore.Qt.NoPen)
        p.drawEllipse(0, 0, size, size)
        # draw letter
        font = QtGui.QFont("Segoe UI", int(size/2))
        font.setBold(True)
        p.setFont(font)
        p.setPen(QtGui.QColor(fg))
        rect = QtCore.QRectF(0, 0, size, size)
        p.drawText(rect, QtCore.Qt.AlignCenter, letter.upper())
        p.end()
        return pix

class MessageBubble:
    @staticmethod
    def html(sender: str, text: str, is_self: bool, timestamp: str):
        # bubble with timestamp above, left/right align
        bubble_color = BUBBLE_SELF if is_self else BUBBLE_OTHER
        align = "right" if is_self else "left"
        # ensure text HTML-safe by basic replacement
        text = (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br>"))
        html = f"""
        <div style="text-align:{align}; margin:8px 6px;">
          <div style="color:gray; font-size:11px; margin-bottom:4px; text-align:{align};">
            {timestamp}
          </div>
          <div style="display:inline-block; background:{bubble_color};
                      border-radius:12px; padding:8px 12px; max-width:72%;
                      box-shadow: 0 1px 3px rgba(0,0,0,0.12);
                      text-align:left; font-size:13px; color:#111;">
            <b style="margin-right:6px;">{sender}</b> {text}
          </div>
        </div>
        """
        return html

class ChatWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat UI Demo")
        # find icon in same folder if exists, else skip
        import os
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))

        self.resize(900, 600)
        self._dark = False

        # central widget
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QHBoxLayout(central)
        main_layout.setContentsMargins(12,12,12,12)
        main_layout.setSpacing(12)

        # left: chat area
        left_card = QtWidgets.QFrame()
        left_card.setObjectName("left_card")
        left_card.setMinimumWidth(560)
        left_layout = QtWidgets.QVBoxLayout(left_card)
        left_layout.setContentsMargins(10,10,10,10)
        left_layout.setSpacing(8)

        # chat display (QTextEdit read-only)
        self.chat_area = QtWidgets.QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setObjectName("chat_area")
        self.chat_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        left_layout.addWidget(self.chat_area, 1)

        # input row
        input_row = QtWidgets.QHBoxLayout()
        self.input_line = QtWidgets.QLineEdit()
        self.input_line.setPlaceholderText("Nhập tin nhắn...")
        self.input_line.returnPressed.connect(self.on_send_clicked)
        self.send_btn = QtWidgets.QPushButton("Gửi")
        self.send_btn.setObjectName("send_btn")
        self.send_btn.clicked.connect(self.on_send_clicked)
        input_row.addWidget(self.input_line, 1)
        input_row.addWidget(self.send_btn, 0)
        left_layout.addLayout(input_row)

        # right: user list + controls
        right_card = QtWidgets.QFrame()
        right_card.setObjectName("right_card")
        right_layout = QtWidgets.QVBoxLayout(right_card)
        right_layout.setContentsMargins(6,6,6,6)
        title_row = QtWidgets.QHBoxLayout()
        lbl = QtWidgets.QLabel("👥 Người đang online")
        lbl.setStyleSheet("font-weight:600;")
        title_row.addWidget(lbl)
        title_row.addStretch()
        # theme toggle
        self.theme_btn = QtWidgets.QPushButton("🌙")
        self.theme_btn.setFixedSize(28,28)
        self.theme_btn.clicked.connect(self.toggle_theme)
        title_row.addWidget(self.theme_btn)
        right_layout.addLayout(title_row)

        # user list
        self.user_list = QtWidgets.QListWidget()
        self.user_list.setObjectName("user_list")
        self.user_list.setIconSize(QtCore.QSize(36,36))
        self.user_list.itemDoubleClicked.connect(self.on_user_double_clicked)
        right_layout.addWidget(self.user_list, 1)

        # footer (status)
        footer = QtWidgets.QHBoxLayout()
        self.status_lbl = QtWidgets.QLabel("Sẵn sàng")
        footer.addWidget(self.status_lbl)
        footer.addStretch()
        right_layout.addLayout(footer)

        main_layout.addWidget(left_card, 3)
        main_layout.addWidget(right_card, 1)

        # style
        self.apply_styles()

        # demo users (you can populate from server)
        self.add_user("Nhan", online=True)
        self.add_user("minh", online=True)
        self.add_user("thao", online=True)

        # For demo: add some initial messages
        self.append_message("SERVER", "Nhan đã tham gia phòng chat", is_self=False, is_system=True)
        self.append_message("Bạn", "Hi there — thử giao diện bong bóng :) ", is_self=True)
        self.append_message("thao", "Hello bạn!", is_self=False)

    def apply_styles(self):
        # global style sheet (light + modifications handled in toggle)
        stylesheet = f"""
        QWidget {{
            background-color: {LIGHT_BG};
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 13px;
            color: #111;
        }}
        QFrame#left_card {{
            background: {CARD_BG};
            border-radius: 10px;
        }}
        QFrame#right_card {{
            background: white;
            border-radius: 10px;
            padding: 6px;
        }}
        QTextEdit#chat_area {{
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                          stop:0 #ffffff, stop:1 #e9f0fb);
            border-radius: 10px;
            padding: 10px;
        }}
        QLineEdit {{
            border: 1.5px solid #cfe8ff;
            border-radius: 10px;
            padding: 8px;
            background: white;
        }}
        QPushButton#send_btn {{
            background-color: {PRIMARY};
            color: white;
            border-radius: 10px;
            padding: 8px 12px;
            font-weight: 700;
        }}
        QPushButton#send_btn:hover {{
            background-color: #005bb5;
        }}

        QListWidget#user_list {{
            background: transparent;
            border: none;
            padding: 4px;
        }}
        QListWidget#user_list::item {{
            padding: 8px;
            border-radius: 8px;
        }}
        QListWidget#user_list::item:hover {{
            background-color: #eaf6ff;
        }}
        QListWidget#user_list::item:selected {{
            background: transparent;
        }}
        """
        self.setStyleSheet(stylesheet)
        self.update_theme_icon()

    def toggle_theme(self):
        self._dark = not self._dark
        if self._dark:
            # apply dark theme tweaks
            dark_css = f"""
            QWidget {{ background: {DARK_BG}; color: {DARK_TEXT}; }}
            QFrame#left_card {{ background: {DARK_CARD}; }}
            QFrame#right_card {{ background: #252525; }}
            QTextEdit#chat_area {{ background: #111214; color: {DARK_TEXT}; }}
            QLineEdit {{ background: #1e1e1e; color: {DARK_TEXT}; border: 1px solid #3a3a3a; }}
            QPushButton#send_btn {{ background-color: #2a9df4; }}
            QListWidget#user_list::item:hover {{ background-color: #2a2a2a; }}
            """
            self.setStyleSheet(self.styleSheet() + dark_css)
        else:
            # reapply light base
            self.apply_styles()
        self.update_theme_icon()

    def update_theme_icon(self):
        self.theme_btn.setText("☀️" if self._dark else "🌙")

    def add_user(self, username, online=True):
        # create item with avatar
        item = QtWidgets.QListWidgetItem(username)
        initial = username[0].upper() if username else "?"
        pix = Avatar.create_pixmap(initial, size=36, bg="#28c840" if online else "#cccccc")
        item.setIcon(QtGui.QIcon(pix))
        # store badge count in data
        item.setData(QtCore.Qt.UserRole, {"unread":0})
        self.user_list.addItem(item)

    def on_user_double_clicked(self, item):
        # open private chat action (demo: append a system line in chat_area)
        username = item.text()
        # clear selection immediate (don't keep blue background)
        self.user_list.clearSelection()
        self.append_message("SYSTEM", f"Opening private chat with {username}", is_self=False, is_system=True)

    def on_send_clicked(self):
        text = self.input_line.text().strip()
        if not text:
            return
        # Normally here you'd send to server; for demo we append locally
        self.append_message("Bạn", text, is_self=True)
        self.input_line.clear()
        # demo: echo from "thao" after short delay
        QtCore.QTimer.singleShot(600, lambda: self.append_message("thao", f"Echo: {text}", is_self=False))

    def append_message(self, sender, text, is_self=False, is_system=False):
        ts = datetime.now().strftime("%H:%M:%S")
        if is_system:
            # style server/system lines
            html = f"<div style='color:#666; font-style:italic; margin:6px 4px;'>{text}</div>"
        else:
            html = MessageBubble.html(sender, text, is_self, ts)
        # append and auto-scroll
        self.chat_area.append(html)
        QtCore.QTimer.singleShot(10, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        sb = self.chat_area.verticalScrollBar()
        sb.setValue(sb.maximum())

def main():
    app = QtWidgets.QApplication(sys.argv)
    w = ChatWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
