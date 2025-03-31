import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any

# 预定义颜色配置（兼容Windows）
try:
    from colorama import just_fix_windows_console

    just_fix_windows_console()
except ImportError:
    pass

COLORS = {
    'core': {
        'DEBUG': '\033[36m',  # 青色
        'INFO': '\033[94m',  # 亮蓝
        'WARNING': '\033[93m',  # 黄色
        'ERROR': '\033[91m',  # 红色
        'CRITICAL': '\033[95m'  # 紫色
    },
    'client': {
        'DEBUG': '\033[92m',  # 绿色
        'INFO': '\033[94m',  # 蓝色
        'WARNING': '\033[93m',  # 黄色
        'ERROR': '\033[91m',  # 红色
        'CRITICAL': '\033[95m'  # 紫色
    },
    'RESET': '\033[0m'
}


class ColorFormatter(logging.Formatter):
    """带颜色标记的日志格式化器"""

    def __init__(self, logger_type: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.colors = COLORS[logger_type]

    def format(self, record: logging.LogRecord) -> str:
        color = self.colors.get(record.levelname, COLORS['RESET'])
        message = super().format(record)
        return f"{color}{message}{COLORS['RESET']}"


class Logger:
    """双通道日志系统"""

    _instance = None  # 保证单例

    INFO = logging.INFO
    DEBUG = logging.DEBUG
    WARNING = logging.WARNING
    ERROR = logging.ERROR

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 初始化核心日志
        self.core_logger = self._create_logger(
            name="CORE",
            logger_type='core',
            formatter=ColorFormatter('core', fmt="[%(asctime)s] %(name)s_%(levelname)s: %(message)s", datefmt="%H:%M:%S")
        )

        # 初始化客户端日志
        self.client_logger = self._create_logger(
            name="CLIENT",
            logger_type='client',
            formatter=ColorFormatter('client', fmt="[%(asctime)s] %(name)s_%(levelname)s: %(message)s", datefmt="%H:%M:%S")
        )

        # 默认不记录文件
        self._file_handlers: Dict[str, RotatingFileHandler] = {}

    def _create_logger(self, name: str, logger_type: str, formatter: logging.Formatter) -> logging.Logger:
        """创建配置单个日志记录器"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # 控制台输出
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    def configure_file_logging(
            self,
            path: str,
            max_bytes: int = 10 * 1024 * 1024,  # 10MB
            backup_count: int = 5,
            log_level: int = logging.DEBUG
    ) -> None:
        """配置文件日志记录"""
        os.makedirs(os.path.dirname(path), exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))

        # 同时添加到两个记录器
        self.core_logger.addHandler(file_handler)
        self.client_logger.addHandler(file_handler)
        self._file_handlers[path] = file_handler

    def set_level(self, level: int, logger_type: Optional[str] = None) -> None:
        """设置日志级别"""
        if logger_type == 'core':
            self.core_logger.setLevel(level)
        elif logger_type == 'client':
            self.client_logger.setLevel(level)
        else:
            self.core_logger.setLevel(level)
            self.client_logger.setLevel(level)


log_system = Logger()


# 核心日志快捷方法 ---------------------------------------------------
def core_trace(msg: str, *args: Any, **kwargs: Any) -> None:
    log_system.core_logger.debug(msg, *args, **kwargs)  # 使用debug级别实现trace

def core_info(msg: str, *args: Any, **kwargs: Any) -> None:
    log_system.core_logger.info(msg, *args, **kwargs)

def core_warn(msg: str, *args: Any, **kwargs: Any) -> None:
    log_system.core_logger.warning(msg, *args, **kwargs)  # 注意方法名是warning

def core_error(msg: str, *args: Any, **kwargs: Any) -> None:
    log_system.core_logger.error(msg, *args, **kwargs)

def core_fatal(msg: str, *args: Any, **kwargs: Any) -> None:
    log_system.core_logger.critical(msg, *args, **kwargs)  # critical对应fatal

# 客户端日志快捷方法 -------------------------------------------------
def trace(msg: str, *args: Any, **kwargs: Any) -> None:
    log_system.client_logger.debug(msg, *args, **kwargs)  # 修正为client_trace

def info(msg: str, *args: Any, **kwargs: Any) -> None:
    log_system.client_logger.info(msg, *args, **kwargs)

def warn(msg: str, *args: Any, **kwargs: Any) -> None:
    log_system.client_logger.warning(msg, *args, **kwargs)

def error(msg: str, *args: Any, **kwargs: Any) -> None:
    log_system.client_logger.error(msg, *args, **kwargs)

def fatal(msg: str, *args: Any, **kwargs: Any) -> None:
    log_system.client_logger.critical(msg, *args, **kwargs)