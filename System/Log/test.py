from Log import Logger, core_trace, core_info, core_warn, core_error, core_fatal, LogConfig, error

# 初始化配置
LogConfig.initialize(
    console_level=Logger.DEBUG,
    file_config={
        'path': '../../logs/app.log',
        'max_bytes': 10 * 1024 * 1024,
        'backup_count': 5,
        'level': Logger.INFO
    }
)

# 记录核心日志
core_trace("系统初始化开始...")
core_info("核心模块加载完成")

core_trace("系统初始化开始...")
core_info("核心模块加载完成")
core_warn("内存使用超过阈值")
core_error("文件读取失败")
core_fatal("不可恢复错误，即将崩溃")

# 客户端日志
error("库存不足")



try:
    # 业务逻辑
    result = 10 / 0
except Exception as e:

    error("用户操作失败，已记录错误")

# 运行时调整日志级别
LogConfig.set_core_level(Logger.WARNING)