#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片OCR识别脚本

使用PaddleOCR识别图片中的文字

特性：
- 断点续传：启动时检查已有CSV，跳过已处理的图片
- 实时写入：每识别完一张图片立即追加到CSV，无需等待全部完成
- 可随时中断：Ctrl+C 停止后，下次运行自动从断点继续
- 如果图片识别出的文字重复，删除图片
"""
import os
import sys
import re
import argparse
import pandas as pd

from concurrent.futures import ThreadPoolExecutor
import threading

from pathlib import Path
# 添加项目根目录到路径
SCRIPT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPT_DIR))
from libs import config, logger


# _ocr_instance = None
# 全局OCR实例
from paddleocr import PaddleOCR
_ocr_instance = PaddleOCR(
    ocr_version="PP-OCRv4",
    precision='fp16',
    # use_doc_orientation_classify=False, # 通过 use_doc_orientation_classify 参数指定不使用文档方向分类模型
    # use_doc_unwarping=False, # 通过 use_doc_unwarping 参数指定不使用文本图像矫正模型
    # use_textline_orientation=False, # 通过 use_textline_orientation 参数指定不使用文本行方向分类模型
)


def image_ocr(img_path, prev_lines, movie_cur_seconds=0, up_settings=None):
    """
    对单张图片进行OCR识别
    
    Args:
        ocr: OCR实例 (PaddleOCR 或 EasyOCR)
        imgpath: 图片路径
        prev_lines: 之前识别过的文字列表（用于去重）
        movie_cur_seconds: 当前时间戳（用于CSV记录）
        up_settings: UP主配置字典（包含 skip_line_pattern, probability_threshold 等）
        
    Returns:
        tuple: (new_items, new_lines) - 识别结果列表和新文字列表
    """
    # 获取默认配置
    default_config = config.bilibili_up_dict.get("default", {})

    # 从 UP 主配置获取跳过模式和置信度阈值
    if up_settings:
        skip_line_pattern_str = up_settings.get('skip_line_pattern', '')
        probability_threshold = up_settings.get('probability_threshold')
    else:
        skip_line_pattern_str = ''
        probability_threshold = None

    # 使用默认值
    if probability_threshold is None:
        probability_threshold = default_config.get('probability_threshold', 0.93)

    # 编译跳过模式正则
    if skip_line_pattern_str:
        skip_line_pattern = re.compile(skip_line_pattern_str)
    else:
        skip_line_pattern = re.compile(r'^$')  # 默认匹配空字符串

    new_lines = []
    new_items = []

    ocr_result_list = _ocr_instance.predict(img_path)
    for item in ocr_result_list:
        print(item["rec_texts"])
        print(item["rec_scores"]) 

        for index, line in enumerate(item["rec_texts"]):
            probability = item["rec_scores"][index]

            if line in prev_lines:
                pass
            elif probability < probability_threshold or skip_line_pattern.search(line):
                pass
            else:
                new_lines.append(line)
                new_items.append({
                    'movie_cur_seconds': movie_cur_seconds, 
                    'probability': probability, 
                    'line': line}
                )
            
            break
        
    return new_items, new_lines


def _append_to_csv(csv_file: Path, items: list, write_lock: threading.Lock):
    """
    追加识别结果到CSV文件（线程安全）

    Args:
        csv_file: CSV文件路径
        items: 识别结果列表
        write_lock: 写入锁
    """
    if not items:
        return

    with write_lock:
        # 检查文件是否存在，决定是否写入header
        write_header = not csv_file.exists()
        df = pd.DataFrame(items)
        df.to_csv(csv_file, mode='a', header=write_header, index=False, encoding='utf-8')


def get_max_processed_timestamp(csv_file: Path) -> float:
    """
    从已有CSV文件中获取最大已处理时间戳（用于断点续传）

    Args:
        csv_file: CSV文件路径

    Returns:
        float: 最大已处理时间戳，如果文件不存在则返回 -1
    """
    if not csv_file.exists():
        return -1

    try:
        df = pd.read_csv(csv_file)
        return df['movie_cur_seconds'].max()
    except Exception as e:
        logger.warning(f"读取已有CSV文件失败: {e}")
        return -1


def pic_2_text(
    pic_dir: str,
    output_dir: str = None,
    interval: float = 0.5,
    up_settings: dict = None
) -> str:
    """
    识别图片中的文字

    Args:
        pic_dir: 图片目录路径
        output_dir: 输出目录（默认从配置文件读取）
        interval: 截取图片的时间间隔（秒）
        up_settings: UP主配置字典（包含 skip_line_pattern, probability_threshold 等）

    Returns:
        str: CSV文件路径
    """
    pic_dir = Path(pic_dir)
    if not pic_dir.exists():
        raise FileNotFoundError(f"图片目录不存在: {pic_dir}")

    # 确定输出目录
    if output_dir is None:
        # pic_dir : d:\workspace\video-crawl-download-ocr-doc-rag\output\有何高见9527\第01347期_20260401_油价....
        # output_dir : d:\workspace\video-crawl-download-ocr-doc-rag\output\有何高见9527
        output_dir = Path(os.path.dirname(pic_dir))
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # 使用图片目录名作为CSV文件名
    csv_file = output_dir / f"{pic_dir.name}_ocr.csv"

    # 获取最大已处理时间戳（断点续传）
    max_processed_timestamp = get_max_processed_timestamp(csv_file)
    logger.info(f"max_processed_timestamp: {max_processed_timestamp}")

    if max_processed_timestamp >= 0:
        logger.info(f"检测到已有进度，最大已处理时间戳: {max_processed_timestamp}")

    # 查找图片文件
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}
    image_files = [
        f for f in pic_dir.iterdir()
        if f.suffix.lower() in image_extensions
    ]

    if not image_files:
        raise FileNotFoundError(f"目录中找不到图片文件: {pic_dir}")

    # 按文件名排序（假设文件名是时间戳）
    image_files = sorted(image_files, key=lambda x: x.stem)

    logger.info(f"开始OCR识别，图片数量: {len(image_files)}")

    # 用于去重
    prev_lines = []

    # 用于统计总数
    total_items = 0

    # 写入锁和线程池
    write_lock = threading.Lock()
    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = []

        for idx, img_file in enumerate(image_files):
            try:
                # 解析时间戳（文件名作为时间戳）
                try:
                    timestamp = float(img_file.stem)
                except ValueError:
                    logger.warning(f"无法解析时间戳: {img_file.name}")
                    timestamp = idx * interval

                logger.info(f"current timestamp : {timestamp}")

                # 断点续传：跳过已处理的图片
                if timestamp <= max_processed_timestamp:
                    logger.debug(f"跳过已处理: {img_file.name}")
                    continue

                items, lines = image_ocr(str(img_file), prev_lines, timestamp, up_settings)

                # 更新已识别行记录（只保留最近100条，减少内存占用）
                if lines:
                    prev_lines = lines + prev_lines
                    prev_lines = prev_lines[:100]

                if items:
                    total_items += len(items)
                    # 提交异步写入任务
                    futures.append(executor.submit(_append_to_csv, csv_file, items, write_lock))
                    logger.info(f"识别到 {len(items)} 条新文本: {lines[:3]}...")
                else:
                    # 删除image_file
                    os.remove(img_file)

                if idx % 50 == 0:
                    logger.info(f"已识别: {idx + 1} / {len(image_files)}")

            except Exception as e:
                logger.warning(f"识别失败 {img_file}: {e}")

        # 等待所有写入任务完成
        for future in futures:
            future.result()

    logger.info(f"OCR识别完成! 结果保存至: {csv_file}")
    logger.info(f"本次共识别到 {total_items} 条文本")

    return str(csv_file)


def main():
    parser = argparse.ArgumentParser(description="图片OCR识别")
    parser.add_argument("-d", "--dir", required=True, help="图片目录路径")
    parser.add_argument("-o", "--output", help="输出目录路径（默认从配置文件读取）")
    parser.add_argument("-i", "--interval", type=float, default=0.5, help="时间间隔（秒）")
    
    args = parser.parse_args()
    
    pic_2_text(
        pic_dir=args.dir,
        output_dir=args.output,
        interval=args.interval
    )


if __name__ == "__main__":
    main()
