#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
"""
import os
import sys
import tomllib
from pathlib import Path
from typing import Optional


def get_script_dir() -> Path:
    """获取脚本所在目录"""
    return Path(__file__).resolve().parent.parent


SCRIPT_DIR = get_script_dir()
PROJECT_ROOT = SCRIPT_DIR.parent


class Config:
    """配置类"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._bilibili_up_dict = None
        self._load_config()
        self._initialized = True
    
    def _get_config_path(self) -> Path:
        """获取配置文件路径"""
        root = PROJECT_ROOT
        config_path = root / "config" / "config.toml"
        # print(f"config_path: {config_path}")
        if config_path.exists():
            return config_path
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    def _load_config(self):
        """加载配置"""
        config_path = self._get_config_path()
        with config_path.open("rb") as f:
            self._config = tomllib.load(f)
        # print(self._config)
    
    @property
    def log_level(self) -> str:
        """日志级别"""
        return self._config.get("sys", {}).get("log_level", "INFO")
    
    @property
    def output_root(self) -> str:
        """输出根目录"""
        return self._config.get("sys", {}).get(
            "output_root", 
            str(PROJECT_ROOT / "output")
        )

    @property
    def excel_root(self) -> str:
        """UP主Excel目录"""
        return self._config.get("sys", {}).get(
            "excel_root",
            str(PROJECT_ROOT / "output")
        )

    def get_default_output_dir(self, create: bool = True) -> str:
        """获取默认输出目录"""
        if create and not os.path.exists(self.output_root):
            os.makedirs(self.output_root)
        return self.output_root
    
    @property
    def bilibili_up_dict(self) -> dict:
        """获取B站UP主列表
        
        Returns:
            dict: {uploader_id: {uploader: "名称", ...其他配置}}
        """
        return self._config["BILIBILI_UP_INFO"]
        # if self._bilibili_up_dict:
        #     return self._bilibili_up_dict

        # up_dict = {}
        # self.bilibili_up_dict
        # for key, value in self._config.items():
        #     if key.startswith("BILIBILI_UP_INFO."):
        #         # 提取 uploader_id: BILIBILI_UP_INFO.290663424 -> 290663424
        #         uploader_id = key.split(".", 1)[-1]
        #         print(f"uploader_id: {uploader_id}")
        #         up_info = value
        #         up_dict[uploader_id] = up_info
        # self._bilibili_up_dict = up_list
        # return up_dict
    
    def get_up_config(self, uploader_id: str) -> dict:
        """获取某个UP主的配置
        
        Args:
            uploader_id: UP主ID
            
        Returns:
            dict: UP主配置
        """
        return self.bilibili_up_dict.get(uploader_id, {})


# 全局配置实例
config = Config()
