#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
base_knowledge_agent - 基础问答Agent

提供基于知识库的问答功能
"""

import os
import sys
from pathlib import Path
from typing import Optional
from abc import ABC, abstractmethod

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class BaseKnowledgeAgent(ABC):
    """基础问答Agent抽象类"""

    def __init__(self, name: str = "知识问答Agent"):
        """
        初始化Agent

        Args:
            name: Agent名称
        """
        self.name = name
        self.vector_store = None

    @abstractmethod
    def query_knowledge(self, question: str, top_k: int = 5) -> list[dict]:
        """
        查询知识库

        Args:
            question: 问题
            top_k: 返回数量

        Returns:
            匹配结果列表
        """
        pass

    @abstractmethod
    def generate_answer(self, question: str, context: list[dict]) -> str:
        """
        生成答案

        Args:
            question: 问题
            context: 上下文（检索结果）

        Returns:
            生成的答案
        """
        pass

    def answer(self, question: str, top_k: int = 5) -> dict:
        """
        回答问题

        Args:
            question: 问题
            top_k: 检索数量

        Returns:
            包含答案和来源的字典
        """
        # 1. 检索知识库
        results = self.query_knowledge(question, top_k)

        if not results:
            return {
                "answer": "抱歉，我在知识库中没有找到相关信息。",
                "sources": [],
                "question": question
            }

        # 2. 生成答案
        answer = self.generate_answer(question, results)

        # 3. 整理来源
        sources = []
        for r in results:
            sources.append({
                "title": r.get("title", "Unknown"),
                "date": r.get("date", ""),
                "preview": r.get("content_preview", "")[:200]
            })

        return {
            "answer": answer,
            "sources": sources,
            "question": question
        }
