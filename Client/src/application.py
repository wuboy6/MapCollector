import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ui.login import LoginWindow
from ui.normal_main import NormalMainWindow


def main():
    # 创建应用程序实例
    app = QApplication(sys.argv)

    # 登录窗口
    login_window = LoginWindow()

    def on_login_success(user_view):
        """登录成功后启动主窗口"""
        login_window.close()
        main_window = NormalMainWindow(user_view.uid)
        main_window.show()
        # 绑定退出信号
        app.aboutToQuit.connect(main_window.close)

    # 绑定登录信号
    login_window.login_success.connect(on_login_success)
    login_window.show()

    # 设置退出事件
    app.setQuitOnLastWindowClosed(True)

    # 启动应用程序事件循环
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()