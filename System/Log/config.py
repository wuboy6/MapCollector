import logging
from .logger import log_system
from typing import Optional, Dict
import Log

class LogConfig:
    """日志系统配置管理器"""

    @staticmethod
    def initialize(
            console_level: int = logging.INFO,
            file_config: Optional[Dict] = None
    ) -> None:
        """
        初始化日志系统
        :param console_level: 控制台日志级别
        :param file_config: 文件日志配置字典
            Example: {
                'path': 'app.log',
                'max_bytes': 10 * 1024 * 1024,
                'backup_count': 5,
                'level': Log:DEBUG
            }
        """
        # 设置控制台级别
        log_system.set_level(console_level)

        # 配置文件日志
        if file_config:
            log_system.configure_file_logging(
                path=file_config.get('path', 'app.log'),
                max_bytes=file_config.get('max_bytes', 10 * 1024 * 1024),
                backup_count=file_config.get('backup_count', 5),
                log_level=file_config.get('level', logging.DEBUG)
            )

    @staticmethod
    def set_core_level(level: int) -> None:
        """设置核心日志级别"""
        log_system.set_level(level, 'core')

    @staticmethod
    def set_client_level(level: int) -> None:
        """设置客户端日志级别"""
        log_system.set_level(level, 'client')