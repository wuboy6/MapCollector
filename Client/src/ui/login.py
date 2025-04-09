import sys
import requests
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QFrame,
    QVBoxLayout, QHBoxLayout, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap

SERVER_URL = "http://127.0.0.1:8000"  # 修改为你的服务端地址

class UserView:
    """简单的用户视图对象，仅保存UID。"""
    def __init__(self, uid: str):
        self.uid = uid

class LoginWindow(QWidget):
    login_success = pyqtSignal(object)  # 传递UserView对象

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedSize(480, 560)
        self.setWindowTitle("地图收藏家 - 登录")

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        # Header布局
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        header_layout.setAlignment(Qt.AlignCenter)

        logo_label = QLabel(self)
        logo_pixmap = QPixmap("../res/logo.png")
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo_label.setText("[LOGO]")
        logo_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        header_layout.addWidget(logo_label)

        title_wrapper = QVBoxLayout()
        title = QLabel("地图收藏家")
        title.setStyleSheet("""
            QLabel {
                font: bold 28px 'Microsoft YaHei';
                color: #2c3e50;
                margin-top: 12px;
            }
        """)
        subtitle = QLabel("Geographic Collection System")
        subtitle.setStyleSheet("""
            QLabel {
                font: 14px 'Segoe UI';
                color: #7f8c8d;
                margin-top: 6px;
            }
        """)
        title_wrapper.addWidget(title)
        title_wrapper.addWidget(subtitle)
        header_layout.addLayout(title_wrapper)

        main_layout.addLayout(header_layout)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #bdc3c7; margin: 20px 0;")
        main_layout.addWidget(separator)

        # 表单布局
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("请输入注册邮箱")
        self.email_edit.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #ecf0f1;
                border-radius: 6px;
                font: 14px 'Segoe UI';
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        form_layout.addWidget(QLabel("邮箱:"))
        form_layout.addWidget(self.email_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #ecf0f1;
                border-radius: 6px;
                font: 14px 'Segoe UI';
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        form_layout.addWidget(QLabel("密码:"))
        form_layout.addWidget(self.password_edit)

        main_layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        button_layout.setContentsMargins(0, 20, 0, 0)

        login_btn = QPushButton("登 录")
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px 30px;
                border-radius: 6px;
                font: bold 14px 'Microsoft YaHei';
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        login_btn.clicked.connect(self.attempt_login)

        register_btn = QPushButton("注 册")
        register_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 12px 30px;
                border-radius: 6px;
                font: bold 14px 'Microsoft YaHei';
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        register_btn.clicked.connect(self.show_register)

        button_layout.addStretch(1)
        button_layout.addWidget(login_btn)
        button_layout.addWidget(register_btn)
        button_layout.addStretch(1)
        main_layout.addLayout(button_layout)

        footer = QLabel("探索地理之美 · 收藏世界精彩\ndeveloper: wuboy")
        footer.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font: 12px 'Microsoft YaHei';
                qproperty-alignment: AlignCenter;
                padding-top: 20px;
            }
        """)
        main_layout.addWidget(footer)

        self.setLayout(main_layout)

    def attempt_login(self):
        email = self.email_edit.text().strip()
        password = self.password_edit.text()

        if not email or not password:
            QMessageBox.warning(self, "输入错误", "邮箱和密码不能为空")
            return

        try:
            data = {"email": email, "password": password}
            response = requests.post(f"{SERVER_URL}/login", json=data)
            if response.status_code == 200:
                result = response.json()
                # 处理登录成功
                user_view = UserView(result["uid"])
                QMessageBox.information(self, "登录成功", f"用户UID: {user_view.uid}")
                self.login_success.emit(user_view)
                self.close()
            else:
                # 登录失败
                err_msg = response.json().get("detail", "未知错误")
                QMessageBox.critical(self, "登录失败", err_msg)
        except Exception as e:
            QMessageBox.critical(self, "系统错误", f"登录出现异常: {str(e)}")

    def show_register(self):
        from src.ui.register import RegisterWindow  # 需要在同级目录下创建register_window.py
        self.register_window = RegisterWindow()
        self.register_window.register_success.connect(self.handle_register_success)
        self.register_window.show()

    def handle_register_success(self, email):
        self.email_edit.setText(email)
        self.password_edit.setFocus()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())