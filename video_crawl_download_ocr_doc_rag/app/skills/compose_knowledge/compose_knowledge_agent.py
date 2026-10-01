#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ComposeKnowledgeAgent - 有何高见文章整理Agent

通过LLM将CSV字幕整理成有段落，有标准标点的markdown文章
"""

import os
import re
from pathlib import Path
from typing import Optional

import pandas as pd
import requests


class ComposeKnowledgeAgent:
    """有何高见文章整理Agent"""

    def __init__(self):
        """初始化Agent"""
        self.llm_config = {
            "auth_token": os.environ.get("ANTHROPIC_AUTH_TOKEN", ""),
            "base_url": "https://qianfan.baidubce.com/anthropic/v1",
            "model": os.environ.get("ANTHROPIC_MODEL", "minimax-m2.5"),
        }

    def read_csv_content(self, csv_file: str) -> str:
        """通过pandas DataFrame读取CSV，返回line列的内容"""
        df = pd.read_csv(csv_file)
        lines = df[df['line'] != 'line']['line'].tolist()
        return '\n'.join(lines)

    def extract_title_from_filename(self, csv_file: str) -> tuple[str, str]:
        """从CSV文件名提取标题和日期"""
        filename = Path(csv_file).stem
        filename = re.sub(r'_ocr$', '', filename)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        date = date_match.group(1) if date_match else ""
        title = re.sub(r'^\d{4}-\d{2}-\d{2}\s*', '', filename).strip()
        return title, date

    def _load_prompt(self) -> str:
        """加载prompt文件"""
        prompt_file = Path(__file__).parent / "compose_knowledge_agent.prompt"
        if prompt_file.exists():
            return prompt_file.read_text(encoding='utf-8').strip()
        # fallback
        return """你是一位专业的文章整理专家。..."""

    def call_llm(self, content: str, title: str, date: str) -> Optional[str]:
        """直接调用LLM API"""
        url = f"{self.llm_config['base_url']}/messages"

        headers = {
            "Authorization": f"Bearer {self.llm_config['auth_token']}",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        # 加载system prompt
        system_prompt = self._load_prompt()

        user_prompt = f"""视频标题：{title}
视频日期：{date}

字幕内容：
{content[:12000]}

请整理成有段落，有标准标点的markdown文章格式。"""

        payload = {
            "model": self.llm_config["model"],
            "max_tokens": 8000,
            "temperature": 0.3,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ]
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=180)
            if response.status_code != 200:
                print(f"API错误: {response.status_code} - {response.text[:200]}")
                return None

            result = response.json()
            text_content = ""
            for block in result.get("content", []):
                if block.get("type") == "text":
                    text_content += block.get("text", "")

            return text_content

        except Exception as e:
            print(f"LLM调用失败: {e}")
            return None

    def simple_compose(self, content: str, title: str, date: str) -> str:
        """简单整理（LLM失败时使用）"""
        filler_words = ['啊', '嗯', '这个', '那个', '就是', '对吧', '是吧', '然后']
        for w in filler_words:
            content = content.replace(w, '')

        lines = [l for l in content.split('\n') if len(l) > 15]

        return f"""## {title}

### 背景
本视频发布于{date}。

### 核心内容
{chr(10).join(lines[:10])}
"""

    def compose(self, csv_file: str, related_materials: Optional[str] = None) -> str:
        """
        整理文章

        Args:
            csv_file: CSV文件路径
            related_materials: 相关材料（可选）

        Returns:
            生成的Markdown文件路径
        """
        # 读取CSV内容
        content = self.read_csv_content(csv_file)
        if not content:
            raise ValueError(f"CSV文件为空: {csv_file}")

        # 提取标题和日期
        title, date = self.extract_title_from_filename(csv_file)

        # 调用LLM
        md_content = self.call_llm(content, title, date)

        if not md_content:
            md_content = self.simple_compose(content, title, date)

        # 清理markdown代码块
        if "```markdown" in md_content:
            start = md_content.find("```markdown") + len("```markdown")
            end = md_content.find("```", start)
            md_content = md_content[start:end].strip()
        elif "```" in md_content:
            start = md_content.find("```") + 3
            end = md_content.find("```", start)
            if end > start:
                md_content = md_content[start:end].strip()

        # 添加frontmatter
        frontmatter = f"""---
title: {title}
date: {date}
source: 有何高见9527
---

"""
        md_content = frontmatter + md_content

        # 保存文件
        output_path = csv_file.replace('_ocr.csv', '.md')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"✓ 已生成文章: {output_path}")
        return output_path


if __name__ == '__main__':
    # 测试
    agent = ComposeKnowledgeAgent()
    agent.compose("doc/有何高见9527/2026.01-06/2026-06-16 699 流动性紧张趋势会得到改善吗？近期市场情绪修复是否昙花一现？_ocr.csv")
