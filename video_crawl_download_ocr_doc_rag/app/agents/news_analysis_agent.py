#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
news_analysis_agent - 新闻分析Agent

读取新的网页内容，分析对未来政治、经济、金融的影响
"""

import os
import sys
from pathlib import Path
from typing import Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class NewsAnalysisAgent:
    """新闻分析Agent"""

    def __init__(self, name: str = "新闻分析Agent"):
        """
        初始化Agent

        Args:
            name: Agent名称
        """
        self.name = name

    def fetch_content(self, url: str) -> str:
        """
        获取网页内容

        Args:
            url: 网页URL

        Returns:
            网页内容
        """
        # 简化版：使用curl获取
        import subprocess
        result = subprocess.run(
            ['curl', '-s', url],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout

    def extract_text(self, html: str) -> str:
        """
        从HTML提取正文

        Args:
            html: HTML内容

        Returns:
            提取的文本
        """
        # 简化版：移除HTML标签
        import re
        # 移除script和style
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', ' ', text)
        # 清理空白
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def analyze_impact(self, content: str, url: str) -> dict:
        """
        分析新闻影响

        Args:
            content: 新闻内容
            url: 新闻URL

        Returns:
            分析结果
        """
        # 这个方法需要接入LLM来进行深度分析
        # 简化版：基于关键词提取关键信息

        analysis = {
            "url": url,
            "content_preview": content[:1000],
            "key_points": [],
            "affected_areas": [],
            "analysis": ""
        }

        # 提取关键词判断影响领域
        impact_keywords = {
            "政治": ["美国", "中国", "政府", "总统", "选举", "外交"],
            "经济": ["GDP", "增长", "通胀", "就业", "贸易", "出口", "进口"],
            "金融": ["股市", "美联储", "降息", "利率", "汇率", "债券"],
            "产业": ["AI", "电动车", "芯片", "能源", "房地产"]
        }

        for area, keywords in impact_keywords.items():
            for kw in keywords:
                if kw in content:
                    if area not in analysis["affected_areas"]:
                        analysis["affected_areas"].append(area)
                    break

        # 提取关键句子
        sentences = content.split('。')
        for sent in sentences:
            if len(sent) > 20 and len(sent) < 100:
                # 包含关键信息的句子
                for kw in ["影响", "分析", "认为", "预计", "可能"]:
                    if kw in sent:
                        analysis["key_points"].append(sent.strip())
                        break

        analysis["key_points"] = analysis["key_points"][:5]  # 最多5条

        return analysis

    def analyze_with_knowledge_base(self, url: str) -> dict:
        """
        结合知识库分析新闻

        Args:
            url: 新闻URL

        Returns:
            分析结果
        """
        # 1. 获取网页内容
        html = self.fetch_content(url)

        if not html:
            return {
                "error": "无法获取网页内容",
                "url": url
            }

        # 2. 提取正文
        content = self.extract_text(html)

        # 3. 分析影响
        analysis = self.analyze_impact(content, url)

        # 4. 检索知识库相关文档（如果可用）
        try:
            from app.skills.vectorize_knowledge.main import VectorizeKnowledge
            vk = VectorizeKnowledge()

            # 从内容中提取关键词进行检索
            keywords = []
            for area in analysis["affected_areas"]:
                keywords.append(area)

            if keywords:
                query_text = " ".join(keywords[:3])
                related_docs = vk.query(query_text, top_k=3)
                analysis["related_knowledge"] = related_docs

        except Exception as e:
            analysis["knowledge_base_error"] = str(e)

        return analysis


def analyze_news(url: str) -> dict:
    """
    新闻分析接口

    Args:
        url: 新闻URL

    Returns:
        分析结果
    """
    agent = NewsAnalysisAgent()
    return agent.analyze_with_knowledge_base(url)


if __name__ == '__main__':
    # 测试
    url = "https://www.cls.cn/detail/2399516"
    result = analyze_news(url)
    print(f"\nURL: {result.get('url')}")
    print(f"\n影响领域: {', '.join(result.get('affected_areas', []))}")
    print(f"\n关键观点:")
    for p in result.get('key_points', [])[:3]:
        print(f"- {p}")
