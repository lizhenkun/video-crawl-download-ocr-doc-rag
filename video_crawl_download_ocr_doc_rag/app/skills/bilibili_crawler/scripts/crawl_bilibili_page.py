#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬取B站视频页面HTML
使用DrissionPage模拟浏览器访问

用法:
    python scripts/crawl_bilibili_page.py -u "https://www.bilibili.com/video/BV15fXpBdE1d/"
    python scripts/crawl_bilibili_page.py -u "BV15fXpBdE1d"
    python scripts/crawl_bilibili_page.py -u "BV15fXpBdE1d" -o "D:\workspace\video-crawl-download-ocr-doc-rag\output" --up "有何高见9527"
"""
import os
import time
import argparse
from pathlib import Path
from typing import Optional

import sys
from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from libs import config, logger, BilibiliPageCrawler
from libs.rename_video import replace_unsuitable_letter


def crawl_page(url: str, output_dir: str = None, uploader: str = None) -> Optional[str]:
    """爬取页面HTML
    
    Args:
        url: B站视频URL或bvid
        output_dir: 输出目录（默认为配置中的output目录）
        headless: 是否使用无头模式
        uploader: UP主名称（可选，指定后会创建UP主文件夹）
    """
    # 获取默认输出目录
    if output_dir is None:
        output_dir = config.output_root
    
    # 如果指定了UP主，创建UP主子文件夹
    if uploader:
        output_dir = os.path.join(output_dir, uploader)

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    page_result = BilibiliPageCrawler.crawl_video_page(url)
    if not page_result:
        logger.error("无法提取bvid")
        return None
    
    title = page_result["title"]
    file_name = replace_unsuitable_letter(title)

    html = page_result["html"]

    # 保存HTML文件
    output_file = os.path.join(output_dir, f"{file_name}.html")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    logger.success(f"HTML已保存: {output_file}")
    logger.info(f"文件大小: {len(html) / 1024:.2f} KB")
    
    return output_file
    

def main():
    """主入口"""
    # 获取默认输出目录
    output_dir = config.output_root
    
    parser = argparse.ArgumentParser(description="爬取B站视频页面HTML")
    parser.add_argument("-u", "--url", type=str, required=True, help="B站视频URL或bvid")
    parser.add_argument("-o", "--output", type=str, default=None, help=f"输出目录 (默认: {output_dir})")
    parser.add_argument("--up", type=str, default=None, help="UP主名称（可选，指定后会创建UP主文件夹）")
    # parser.add_argument("--headless", action="store_true", help="无头模式运行浏览器")
    
    args = parser.parse_args()
    
    logger.info(f"输入: {args.url}")
    logger.info(f"输出目录: {args.output or output_dir}")
    if args.up:
        logger.info(f"UP主文件夹: {args.up}")
    
    result = crawl_page(args.url, args.output, args.up)
    
    if result:
        logger.success(f"完成! 文件保存至: {result}")
    else:
        logger.error("爬取失败")


if __name__ == "__main__":
    main()
