from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,QFrame,
    QVBoxLayout, QHBoxLayout, QMessageBox, QSpacerItem
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont

class RegisterWindow(QWidget):
    register_success = pyqtSignal(str)  # 传递注册成功的邮箱

    def __init__(self, user_server):
        super().__init__()
        self.user_server = user_server
        self.init_ui()
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedSize(600, 500)  # 调整窗口尺寸
        self.setWindowTitle("地图收藏家 - 注册")

    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(60, 40, 60, 40)
        main_layout.setSpacing(25)

        # 标题区域
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignCenter)
        title_layout.setSpacing(20)

        # Logo
        logo_label = QLabel(self)
        logo_pixmap = QPixmap("../res/logo.png")
        if not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        title_layout.addWidget(logo_label)

        # 文字标题
        title_wrapper = QVBoxLayout()
        title = QLabel("加入地图收藏家")
        title.setStyleSheet("""
            QLabel {
                font: bold 24px 'Microsoft YaHei';
                color: #2c3e50;
            }
        """)
        subtitle = QLabel("Start Your Geographic Journey")
        subtitle.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font: 14px 'Segoe UI';
            }
        """)
        title_wrapper.addWidget(title)
        title_wrapper.addWidget(subtitle)
        title_layout.addLayout(title_wrapper)

        main_layout.addLayout(title_layout)

        # 分割线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("border: 1px solid #ecf0f1; margin: 20px 0;")
        main_layout.addWidget(separator)

        # 表单布局
        form_layout = QVBoxLayout()
        form_layout.setSpacing(20)

        # 邮箱输入
        self.email_edit = QLineEdit()
        self._style_input(self.email_edit, "example@domain.com")
        form_layout.addWidget(QLabel("电子邮箱:"))
        form_layout.addWidget(self.email_edit)

        # 密码输入
        self.password_edit = QLineEdit()
        self._style_input(self.password_edit, "至少8位字符")
        self.password_edit.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(QLabel("设置密码:"))
        form_layout.addWidget(self.password_edit)

        # 确认密码
        self.confirm_edit = QLineEdit()
        self._style_input(self.confirm_edit, "再次输入密码")
        self.confirm_edit.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(QLabel("确认密码:"))
        form_layout.addWidget(self.confirm_edit)

        main_layout.addLayout(form_layout)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        button_layout.setContentsMargins(0, 30, 0, 0)

        # 注册按钮
        register_btn = QPushButton("立即加入")
        register_btn.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2ecc71);
                color: white;
                padding: 14px 40px;
                border-radius: 25px;
                font: bold 16px 'Microsoft YaHei';
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2980b9, stop:1 #27ae60);
            }
            QPushButton:pressed {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2472a4, stop:1 #219653);
            }
        """)
        register_btn.clicked.connect(self.attempt_register)

        # 返回按钮
        cancel_btn = QPushButton("返回登录")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #bdc3c7;
                color: white;
                padding: 12px 30px;
                border-radius: 20px;
                font: bold 14px 'Microsoft YaHei';
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """)
        cancel_btn.clicked.connect(self.close)

        button_layout.addStretch(1)
        button_layout.addWidget(register_btn)
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch(1)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _style_input(self, widget, placeholder):
        """统一输入框样式"""
        widget.setPlaceholderText(placeholder)
        widget.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #ecf0f1;
                border-radius: 8px;
                font: 14px 'Segoe UI';
                background: #ffffff;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background: #f8f9fa;
            }
        """)
        widget.setMinimumHeight(40)


    def attempt_register(self):
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        confirm = self.confirm_edit.text()

        # 前端验证
        errors = []
        if not email:
            errors.append("邮箱不能为空")
        if "@" not in email:
            errors.append("邮箱格式不正确")
        if not password:
            errors.append("密码不能为空")
        if password != confirm:
            errors.append("两次输入的密码不一致")

        if errors:
            QMessageBox.warning(self, "注册错误", "\n".join(errors))
            return

        # 调用服务
        status, uid = self.user_server.register(email, password)

        if status == 0:
            QMessageBox.information(self, "注册成功", "账户创建成功，请返回登录")
            self.register_success.emit(email)
            self.close()
        elif status == 2002:
            QMessageBox.warning(self, "注册失败", "该邮箱已被注册")
            self.email_edit.setFocus()
        elif status == 3001:
            QMessageBox.warning(self, "密码强度不足", "请使用更复杂的密码组合")
            self.password_edit.setFocus()
        else:
            QMessageBox.critical(self, "系统错误", "注册过程中发生未知错误")