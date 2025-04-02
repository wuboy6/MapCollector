from api.base_api import UserServer, NormalUser, SuperUser, UserView
from api.base_api import trace, info, warn, error, fatal

import sys
from typing import Optional, Type
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSignal, QObject
from api.base_api import MapServer, UserServer
from ui.login import LoginWindow
from ui.normal_main import NormalMainWindow


class AppSignals(QObject):
    """全局信号总线"""
    shutdown = pyqtSignal()


class MapCollectorApp:
    def __init__(self):
        # 应用基础
        self.app = QApplication(sys.argv)
        self.signals = AppSignals()
        self.signals.shutdown.connect(self._cleanup)

        # 服务层
        self.user_server = UserServer()
        self.map_server = self.user_server.map_server

        # 用户状态
        self.current_user: NormalUser|SuperUser|None = None

        # 初始化界面路由
        self._init_ui()

    def _init_ui(self):

        """初始化界面层级"""
        self.login_window = LoginWindow(self.user_server)
        self.login_window.login_success.connect(self._handle_auth_success)
        self.login_window.show()

        self.main_window: Optional[NormalMainWindow] = None

    def _handle_auth_success(self, user_view: UserView):
        """认证成功处理"""
        self.current_user = user_view
        self._launch_main_ui()
        self.login_window.close()

    def _launch_main_ui(self):
        """启动主界面"""
        if self.current_user is None:
            return

        self.main_window = NormalMainWindow(
            user_server=self.user_server,
            map_server=self.map_server,
            current_user=self.current_user,
            signals=self.signals
        )
        self.main_window.show()

    def _cleanup(self):
        """资源清理"""
        # if self.main_window:
        #     self.main_window.close()
        self.user_server.shutdown()
        sys.exit()

    def run(self) -> int:
        """启动应用主循环"""
        return self.app.exec_()


if __name__ == "__main__":
    try:
        ret = MapCollectorApp().run()
        sys.exit(ret)
    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        sys.exit(1)