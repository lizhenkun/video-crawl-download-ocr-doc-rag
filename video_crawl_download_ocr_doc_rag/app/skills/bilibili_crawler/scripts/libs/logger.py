#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
file: logger.py

How to run:
python -m logger
python -m libs.logger

python logger.py
python ./libs/logger.py
python ./scripts/libs/logger.py

How to use : 
from libs import logger
"""
import inspect

from loguru import logger as _logger
from loguru._defaults import env

import sys
from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from libs import config


def _shorten_path(record):
    """截取 app/ 之后的路径"""
    path = record["file"].path.replace(str(SCRIPT_DIR.parent.parent), "")
    record["extra"]["short_path"] = path
    return True


LOGURU_FORMAT = env(
    "LOGURU_FORMAT",
    str,
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    # "<green>{thread.name}</green> | " # 想加 线程 信息 把此处打开
    "<cyan>{extra[short_path]}</cyan>:<cyan>{line}</cyan> | <cyan>{function}</cyan> |"
    "<level>{level: <8}</level> | "
    "<level>{message}</level>",
)


def get_default_logger(name: str = None):
    """Adjust the log level to above level"""
    _logger.remove()
    _logger.add(
        sys.stderr, level=config.log_level, 
        format=LOGURU_FORMAT, filter=_shorten_path)
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
        
        file_name = caller.filename.replace(str(SCRIPT_DIR.parent.parent), ".").strip()
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
    logger.info("THIS IS A INFO LOG")
    logger.debug("THIS IS A DEBUG LOG")
    logger.warning("THIS IS A WARNING LOG")
    logger.error("THIS IS AN ERROR LOG")
    logger.critical("THIS IS A CRITICAL LOG")

    try:
        raise ValueError("RAISE VALUE ERROR FOR TEST PURPOSE")
    except Exception as e:
        logger.exception(f"THIS IS AN EXCEPTION LOG: {e}")
    
    _test()
