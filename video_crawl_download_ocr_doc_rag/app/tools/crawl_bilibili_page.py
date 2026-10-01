#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬取B站视频页面HTML
使用DrissionPage模拟浏览器访问

用法:
    python -m app.tools.crawl_bilibili_page -u "https://www.bilibili.com/video/BV15fXpBdE1d/"
    python -m app.tools.crawl_bilibili_page -u "BV15fXpBdE1d"
"""
import os
import re
import argparse
from pathlib import Path
from typing import Optional

from DrissionPage import ChromiumPage, ChromiumOptions

from app.config import config


def extract_bvid(url: str) -> Optional[str]:
    """从URL提取bvid"""
    if url.startswith("BV") and len(url) == 12:
        return url
    
    patterns = [
        r'bilibili\.com/video/(BV[\w]+)',
        r'BV[\w]{10}',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1) if match.lastindex else match.group(0)
    return None


def crawl_page(url: str, output_dir: str = "output") -> Optional[str]:
    """爬取页面HTML"""
    # 提取bvid
    bvid = extract_bvid(url)
    if not bvid:
        print("无法提取bvid")
        return None
    
    # 构建完整URL
    if not url.startswith("http"):
        url = f"https://www.bilibili.com/video/{bvid}/"
    
    print(f"正在访问: {url}")
    
    # 创建浏览器实例
    driver = ChromiumPage(config.CHROMIUM_OPTIONS)
    
    try:
        # 访问页面
        driver.get(url)
        
        # 等待页面加载
        print("等待页面加载...")
        driver.wait.load_start()
        
        # 等待一段时间确保内容加载完成
        import time
        time.sleep(3)
        
        # 获取页面HTML (尝试多种属性)
        try:
            html = driver.page_html
        except AttributeError:
            try:
                html = driver.html
            except AttributeError:
                html = driver.get_tab(0).html
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存HTML文件
        output_file = os.path.join(output_dir, f"{bvid}.html")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"HTML已保存: {output_file}")
        print(f"文件大小: {len(html) / 1024:.2f} KB")
        
        return output_file
    
    finally:
        driver.quit()


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="爬取B站视频页面HTML")
    parser.add_argument("-u", "--url", type=str, required=True, help="B站视频URL或bvid")
    parser.add_argument("-o", "--output", type=str, default="output", help="输出目录 (默认output)")
    
    args = parser.parse_args()
    
    print(f"{'='*60}")
    print(f"输入: {args.url}")
    print('='*60)
    
    result = crawl_page(args.url, args.output)
    
    if result:
        print(f"\n完成! 文件保存至: {result}")
    else:
        print("\n失败")


if __name__ == "__main__":
    main()
