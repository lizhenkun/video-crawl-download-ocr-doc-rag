#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compose_knowledge v2 - 有何高见文章整理CLI入口 (直接导入版)

使用方法:
    python main_v2.py --csv "xxx_ocr.csv"
    python main_v2.py --dir "目录路径"

主要变更:
- 直接导入 Agent 类，不使用 importlib 动态加载
- 加载外部 prompt 文件
"""

import argparse
import os
import sys
import importlib
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_prompt(prompt_file: str) -> str:
    """加载外部prompt文件"""
    prompt_path = Path(__file__).parent / prompt_file
    if prompt_path.exists():
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='有何高见文章整理 (v2版)')
    parser.add_argument('--csv', help='CSV文件路径')
    parser.add_argument('--dir', help='批量处理目录')
    parser.add_argument('--materials', help='相关背景材料')
    parser.add_argument('--prompt', default='compose_knowledge_agent.prompt', help='Prompt文件')

    args = parser.parse_args()

    # 加载prompt
    prompt_content = load_prompt(args.prompt)
    if prompt_content:
        print(f"✓ 已加载prompt: {args.prompt}")

    # 直接导入Agent
    from video_crawl_download_ocr_doc_rag.app.skills.compose_knowledge.compose_knowledge_agent import ComposeKnowledgeAgent

    agent = ComposeKnowledgeAgent()

    # 可选：设置自定义prompt（如果需要）
    if prompt_content:
        agent.custom_prompt = prompt_content

    if args.csv:
        agent.compose(args.csv, args.materials)
    elif args.dir:
        # 批量处理
        results = []
        for root, dirs, files in os.walk(args.dir):
            for file in files:
                if file.endswith('_ocr.csv'):
                    csv_path = os.path.join(root, file)
                    try:
                        output_path = agent.compose(csv_path)
                        results.append(output_path)
                    except Exception as e:
                        print(f"✗ 处理失败 {csv_path}: {e}")
        print(f"\n共处理 {len(results)} 个文件")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
