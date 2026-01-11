import inspect
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from .config import settings

def setup_logging():
    # 确保日志目录存在
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    # 日志格式
    formatter = logging.Formatter(
        f'{settings.LOG_FORMAT}'
    )

    # 控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setLevel(settings.LOG_LEVEL)
    console_handler.setFormatter(formatter)

    # 文件日志处理器
    file_handlers = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warn': logging.WARNING,
        'error': logging.ERROR
    }

    # 主日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # 设置最低级别

    # 添加控制台处理器
    root_logger.addHandler(console_handler)

    # 为每个级别创建文件处理器
    for level_name, level in file_handlers.items():
        file_path = log_dir / f"{level_name}.log"
        handler = RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        handler.setLevel(level)
        handler.setFormatter(formatter)

        # 添加过滤器只处理特定级别日志
        if level_name == 'debug':
            handler.addFilter(lambda record: record.levelno == logging.DEBUG)
        elif level_name == 'info':
            handler.addFilter(lambda record: record.levelno == logging.INFO)
        elif level_name == 'warn':
            handler.addFilter(lambda record: record.levelno == logging.WARNING)
        elif level_name == 'error':
            handler.addFilter(lambda record: record.levelno >= logging.ERROR)

        root_logger.addHandler(handler)

    # SQL日志特殊处理
    if settings.LOG_LEVEL == "DEBUG" and settings.SQL_DEBUG:
        sql_logger = logging.getLogger('sqlalchemy.engine')
        sql_logger.setLevel(logging.DEBUG)

        sql_handler = RotatingFileHandler(
            log_dir / "sql.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=2,
            encoding='utf-8'
        )
        sql_handler.setFormatter(formatter)
        sql_logger.addHandler(sql_handler)


setup_logging()


class CallerLogger(logging.Logger):
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        super().__init__(logger.name, logger.level)

    def _log(self, level, msg, args, exc_info=None, extra=None, stacklevel=3):
        if self.logger.isEnabledFor(level):
            self.logger._log(level, msg, args, exc_info=exc_info, extra=extra, stacklevel=stacklevel)


class TerraLogUtil:

    @staticmethod
    def _get_logger() -> logging.Logger:
        frame = inspect.currentframe()
        try:
            caller_frame = frame.f_back.f_back
            module_name = caller_frame.f_globals.get('__name__', '__main__')
            return CallerLogger(logging.getLogger(module_name))
        finally:
            del frame

    @staticmethod
    def debug(msg: str, *args, **kwargs):
        logger = TerraLogUtil._get_logger()
        if logger.isEnabledFor(logging.DEBUG):
            logger._log(logging.DEBUG, msg, args, **kwargs)

    @staticmethod
    def info(msg: str, *args, **kwargs):
        logger = TerraLogUtil._get_logger()
        if logger.isEnabledFor(logging.INFO):
            logger._log(logging.INFO, msg, args, **kwargs)

    @staticmethod
    def warning(msg: str, *args, **kwargs):
        logger = TerraLogUtil._get_logger()
        if logger.isEnabledFor(logging.WARNING):
            logger._log(logging.WARNING, msg, args, **kwargs)

    @staticmethod
    def error(msg: str, *args, exc_info: Optional[bool] = None, **kwargs):
        logger = TerraLogUtil._get_logger()
        if logger.isEnabledFor(logging.ERROR):
            logger._log(
                logging.ERROR,
                msg,
                args,
                exc_info=exc_info if exc_info is not None else True,
                **kwargs
            )

    @staticmethod
    def exception(msg: str, *args, **kwargs):
        logger = TerraLogUtil._get_logger()
        if logger.isEnabledFor(logging.ERROR):
            logger._log(logging.ERROR, msg, args, exc_info=True, **kwargs)

    @staticmethod
    def critical(msg: str, *args, **kwargs):
        logger = TerraLogUtil._get_logger()
        if logger.isEnabledFor(logging.CRITICAL):
            logger._log(logging.CRITICAL, msg, args, **kwargs)

