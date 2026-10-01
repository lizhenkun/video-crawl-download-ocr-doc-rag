#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compose_knowledge - 有何高见文章整理入口

使用方法:
    单个文件: python main.py --csv "xxx_ocr.csv"
    批量目录: python main.py --dir "目录路径"
"""

import argparse
import os
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入Agent类
import importlib.util
spec = importlib.util.spec_from_file_location(
    "compose_knowledge_agent",
    Path(__file__).parent / "compose_knowledge_agent.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ComposeKnowledgeAgent = module.ComposeKnowledgeAgent


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='有何高见文章整理')
    parser.add_argument('--csv', help='CSV文件路径')
    parser.add_argument('--dir', help='批量处理目录')
    parser.add_argument('--materials', help='相关背景材料')

    args = parser.parse_args()

    agent = ComposeKnowledgeAgent()

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
