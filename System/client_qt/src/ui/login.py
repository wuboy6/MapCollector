from api.base_api import trace, info, warn, error, fatal
from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,QFrame,
    QVBoxLayout, QHBoxLayout, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from api.base_api import UserServer, NormalUser, SuperUser, UserView

class LoginWindow(QWidget):
    login_success = pyqtSignal(object)  # 传递UserView对象

    def __init__(self, user_server):
        super().__init__()
        self.user_server = user_server
        self.init_ui()
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedSize(480, 560)  # 增大窗口尺寸
        self.setWindowTitle("地图收藏家 - 登录")  # 添加窗口标题

    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        # 横向Logo和标题布局
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        header_layout.setAlignment(Qt.AlignCenter)

        # Logo区域
        logo_label = QLabel(self)
        logo_pixmap = QPixmap("../res/logo.png")  # 建议尺寸160x160
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo_label.setText("[LOGO]")
        logo_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        header_layout.addWidget(logo_label)

        # 标题区域
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

        # 分割线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #bdc3c7; margin: 20px 0;")
        main_layout.addWidget(separator)

        # 表单布局（保持原有样式不变）
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)

        # 邮箱输入
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

        # 密码输入
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

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        button_layout.setContentsMargins(0, 20, 0, 0)

        # 登录按钮
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

        # 注册按钮
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

        # 底部信息
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
            if email == "2287401905@qq.com":
                user_view = self.user_server.register_user(email, password, SuperUser)
                if user_view:
                    info(f"超级用户登录成功: {email}")
                    self.login_success.emit(user_view)
                    self.close()
                else:
                    QMessageBox.critical(self, "登录失败", "无效的邮箱或密码")
            else:
                user_view = self.user_server.register_user(email, password, NormalUser)
                if user_view:
                    info(f"用户登录成功: {email}")
                    self.login_success.emit(user_view)
                    self.close()
                else:
                    QMessageBox.critical(self, "登录失败", "无效的邮箱或密码")
        except Exception as e:
            error(f"登录异常: {str(e)}")
            QMessageBox.critical(self, "系统错误", "登录服务暂时不可用")

    def show_register(self):
        from ui.register import RegisterWindow  # 延迟导入避免循环依赖
        self.register_window = RegisterWindow(self.user_server)
        self.register_window.register_success.connect(self.handle_register_success)
        self.register_window.show()

    def handle_register_success(self, email):
        self.email_edit.setText(email)
        self.password_edit.setFocus()