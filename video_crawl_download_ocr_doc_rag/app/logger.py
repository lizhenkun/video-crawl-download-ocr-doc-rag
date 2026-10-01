#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
file: logger.py
"""
import sys
import inspect
from datetime import datetime

from loguru import logger as _logger
from loguru._defaults import env

from app.config import config
from app.config import PROJECT_ROOT


LOGURU_FORMAT = env(
    "LOGURU_FORMAT",
    str,
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    # "<green>{thread.name}</green> | " # 想加 线程 信息 把此处打开
    "<level>{level: <8}</level> | "
    "<cyan>{file.path}</cyan>:<cyan>{line}</cyan> | <cyan>{function}</cyan> - <level>{message}</level>",
)


def get_default_logger(name: str = None):
    """Adjust the log level to above level"""
    current_date = datetime.now()
    # 按分钟生成日志
    # formatted_date = current_date.strftime("%Y%m%d%H%M%S")

    # 按天
    formatted_date = current_date.strftime("%Y%m%d")

    log_name = (
        f"{name}.{formatted_date}" if name else formatted_date
    )  # name a log with prefix name

    _logger.remove()
    _logger.add(sys.stderr, level=config.print_level, format=LOGURU_FORMAT)
    _logger.add(PROJECT_ROOT / f"log/{log_name}.log", level=config.log_level, format=LOGURU_FORMAT)
    return _logger

logger = get_default_logger()


def __get_calleres(stack_depth: int=3, begin_index: int=0):
    """
    get calleres
    """
    calleres = []

    for index in range(begin_index + stack_depth, begin_index, -1):
        # 获取调用栈，索引0是当前帧，索引1是调用者
        caller_frame = inspect.stack()[index + 1]
        # filename , lineno
        calleres.append(caller_frame)

    return calleres


def print_caller_stack(msg="", stack_depth: int=3, begin_index: int=0, level="debug"):
    """
    打印调用函数信息
    """
    calleres = __get_calleres(stack_depth=stack_depth, begin_index=begin_index)
    
    stack_msg = "\n"

    for index, caller in enumerate(calleres):
        if index > 0:
            stack_msg += f" -->\n"
        
        file_name = caller.filename.replace(str(PROJECT_ROOT), "").strip()
        if file_name[0] in ["/", "\\"]:
            file_name = file_name[1:]

        stack_msg += f'depth: {stack_depth - index} | file: {file_name}:{caller.lineno} | func: {caller.function}'

    print_func = getattr(logger, level)
    if msg:
        stack_msg += f" -->\nlog: {msg}"
    
    print_func(stack_msg)
    return


def _test():
    _test_1()

def _test_1():
    _test_2()

def _test_2():
    _test_3()

def _test_3():
    print_caller_stack(stack_depth=3, begin_index=0)
    _test_4()

def _test_4():
    print_caller_stack("finish", stack_depth=3, begin_index=0)


if __name__ == "__main__":
    logger.info("Starting application")
    logger.debug("Debug message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")

    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
    # python -m app.lib.print_stack
    _test()
