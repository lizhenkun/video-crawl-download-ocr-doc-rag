# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authors: 坤叔(1292746975@qq.com)
参考:
https://blog.csdn.net/qq_39147299/article/details/132236245
"""
import os
import sys
import json
import threading
import tomllib
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from DrissionPage import ChromiumOptions


def get_script_dir() -> Path:
    """Get the project root directory"""
    return Path(__file__).resolve().parent.parent

SCRIPT_DIR = get_script_dir()
PROJECT_ROOT = SCRIPT_DIR.parent


class Config:
    """config class"""
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        
        print(f'{"-" * 60}\n system.args: {sys.argv}\n{"-" * 60}')

        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._config = None
                    self._load_initial_config()
                    self._initialized = True

    @staticmethod
    def _get_config_path() -> Path:
        root = PROJECT_ROOT
        config_path = root / "config" / "config.toml"
        if config_path.exists():
            return config_path

        raise FileNotFoundError("No configuration file found in config directory")

    def _load_config(self) -> dict:
        config_path = self._get_config_path()
        with config_path.open("rb") as f:
            return tomllib.load(f)

    def _load_initial_config(self):
        self._config = self._load_config()
        # print(f'raw_config: {json.dumps(self._config)}')

    @property
    def sys_config(self):
        if "sys" not in self._config:
            self._config["sys"] = {}
        return self._config["sys"]

    @property
    def log_level(self):
        """log level"""
        return self.sys_config.get("log_level", "INFO")
    
    @property
    def brower_config(self):
        return self._config["brower"]
    
    @property
    def headers_config(self):
        return self._config["headers"]
    
    @property
    def bilibili_up_list(self):
        return self._config["BILIBILI_UP_INFO"]
    
    @property
    def output_root(self):
        if "output_root" not in self.sys_config:
            self.sys_config["output_root"] = str(PROJECT_ROOT / "output")

        return self.sys_config["output_root"]
    
    def get_default_output_dir(self, create=True) -> str:
        """从配置获取默认输出目录"""
        if create and not os.path.exists(self.output_root):
            os.makedirs(self.output_root)

        return self.output_root
    
    # WEB_BROWER_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    WEB_BROWER_PATH = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
    # WEB_BROWER_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

    CHROMIUM_OPTIONS = ChromiumOptions().auto_port()
    # CHROMIUM_OPTIONS.set_paths(browser_path=DRIVER_PATH)
    # 设置无痕模式
    # CHROMIUM_OPTIONS.incognito(True)


config = Config()
# print(type(config)) # dict
# print(config["output"]["root"])
