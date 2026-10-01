#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
knowledge_qa_agent - 有何高见知识问答Agent

基于知识库回答关于政治、经济、金融领域的问题
"""

import os
import sys
from pathlib import Path
from typing import Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.agents.base_knowledge_agent import BaseKnowledgeAgent
from app.skills.vectorize_knowledge.main import VectorizeKnowledge


class KnowledgeQAAgent(BaseKnowledgeAgent):
    """有何高见知识问答Agent"""

    def __init__(self, name: str = "有何高见知识问答"):
        """
        初始化Agent

        Args:
            name: Agent名称
        """
        super().__init__(name)
        self.vector_store = VectorizeKnowledge()

    def query_knowledge(self, question: str, top_k: int = 5) -> list[dict]:
        """
        查询知识库

        Args:
            question: 问题
            top_k: 返回数量

        Returns:
            匹配结果列表
        """
        return self.vector_store.query(question, top_k)

    def generate_answer(self, question: str, context: list[dict]) -> str:
        """
        生成答案

        Args:
            question: 问题
            context: 上下文（检索结果）

        Returns:
            生成的答案
        """
        if not context:
            return "抱歉，我没有找到相关信息。"

        # 构建上下文
        context_text = "\n\n".join([
            f"【文档{i+1}】{r.get('title', 'Unknown')}\n{r.get('content_preview', '')}"
            for i, r in enumerate(context)
        ])

        # 简化版：基于检索结果生成回答
        # 实际使用可以接入LLM API
        answer_parts = []

        # 提取核心观点
        for r in context[:3]:
            title = r.get('title', 'Unknown')
            preview = r.get('content_preview', '')

            # 查找核心观点部分
            if '## 核心观点' in preview:
                start = preview.find('## 核心观点')
                section = preview[start:start+500]
                answer_parts.append(f"\n关于这个问题，让我结合「{title}」的分析来回答：")
                answer_parts.append(section)

        if not answer_parts:
            # 如果没有核心观点，使用内容预览
            answer_parts.append("根据知识库中的相关分析：")
            for r in context[:2]:
                answer_parts.append(f"\n- {r.get('title', 'Unknown')}: {r.get('content_preview', '')[:300]}...")

        return "\n".join(answer_parts)


def ask(question: str, top_k: int = 5) -> dict:
    """
    问答接口

    Args:
        question: 问题
        top_k: 检索数量

    Returns:
        问答结果
    """
    agent = KnowledgeQAAgent()
    return agent.answer(question, top_k)


if __name__ == '__main__':
    # 测试
    result = ask("美国为什么无法再像2020年那样印钱救市？")
    print(f"\n问题: {result['question']}")
    print(f"\n答案:\n{result['answer']}")
    print(f"\n来源:")
    for s in result['sources']:
        print(f"- {s['title']} ({s['date']})")
