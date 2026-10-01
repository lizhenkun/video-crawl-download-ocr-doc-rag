#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频转图片脚本

将视频按固定时间间隔截取成图片
"""
import os
import sys
import argparse
from pathlib import Path

import pandas as pd

# 添加项目根目录到路径
SCRIPT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from libs import config, logger
from moviepy import VideoFileClip


def video_2_pic(
    video_path: str,
    interval: float = None,
    crop_y1: int = None,
    crop_y2: int = None,
    output_dir: str = None
) -> str:
    """
    将视频转换为图片

    Args:
        video_path: 视频文件路径
        interval: 截图间隔（秒）
        crop_y1: 裁剪起始Y坐标
        crop_y2: 裁剪结束Y坐标
        output_dir: 输出目录（默认路径: ./视频所在文件夹/视频名字/ ）

    Returns:
        str: 图片保存目录路径
    """
    # 获取默认配置
    default_config = config.bilibili_up_dict.get("default", {})

    # 使用默认值
    interval = interval or default_config.get("interval", 0.5)
    crop_y1 = crop_y1 if crop_y1 is not None else default_config.get("crop_y1", -180)
    crop_y2 = crop_y2 if crop_y2 is not None else default_config.get("crop_y2", -60)
    
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    
    # 确定输出目录：优先使用参数，其次使用配置文件
    if output_dir is None:
        output_dir = Path(os.path.dirname(video_path)) / video_path.stem
    else:
        output_dir = Path(output_dir)

    # # D:\workspace\video-crawl-download-ocr-doc-rag\output\有何高见9527\2026-03-31 647 比亚迪年报发布，有哪些亮点？
    # print(output_dir)
    # # D:\workspace\video-crawl-download-ocr-doc-rag\output\有何高见9527
    # print(os.path.dirname(video_path))
    # # 2026-03-31 647 比亚迪年报发布，有哪些亮点？
    # print(video_path.stem)

    logger.info(f"\ninput: {video_path} \noutput dir:{output_dir}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"开始处理视频: {video_path}")
    logger.info(f"输出目录: {output_dir}")
    logger.info(f"截图间隔: {interval}秒")
    logger.info(f"裁剪参数: y1={crop_y1}, y2={crop_y2}")
    
    # 加载视频
    clip = VideoFileClip(str(video_path))
    
    # 裁剪视频（用于去掉水印）
    if crop_y1 != 0 or crop_y2 != 0:
        clip = clip.cropped(
            y1=clip.h + crop_y1,
            y2=clip.h + crop_y2
        )
    
    duration = clip.duration
    logger.info(f"视频时长: {duration}秒")
    
    # 计算需要截图的数量
    total_frames = int(duration / interval)
    logger.info(f"预计截图数量: {total_frames}")
    
    # 截图
    record_list = []
    cur_time = 0.0
    index = 0
    
    # 时间格式化宽度
    time_width = len(str(int(duration))) + 1
    
    while cur_time < duration:
        # 生成文件名
        index_str = str(index).zfill(time_width + 1)
        png_file = output_dir / f"{index_str}.png"
        
        # 保存帧
        clip.save_frame(str(png_file), t=cur_time)
        
        record_list.append({
            "index": index,
            "time": cur_time,
            "file": png_file,
            "text": ""
        })
        
        if index % 100 == 0:
            logger.info(f"已处理: {cur_time:.1f}s / {duration}s")
        
        cur_time += interval
        index += 1
    
    clip.close()
    
    # 保存索引CSV
    df = pd.DataFrame(record_list)
    csv_file = Path(os.path.dirname(video_path)) / f"{video_path.stem}.csv"
    df.to_csv(csv_file, index=False)
    
    logger.info(f"截图完成! 共 {len(record_list)} 张图片")
    logger.info(f"索引文件: {csv_file}")
    
    return str(output_dir)


def main():
    parser = argparse.ArgumentParser(description="视频转图片")
    parser.add_argument("-i", "--input", required=True, help="输入视频文件路径")
    parser.add_argument("-d", "--dir", help="输出目录路径（默认从配置文件读取）")
    parser.add_argument("--interval", type=float, help="截图间隔（秒）")
    parser.add_argument("--crop-y1", type=int, default=-200, help="裁剪起始Y坐标")
    parser.add_argument("--crop-y2", type=int, default=-30, help="裁剪结束Y坐标")
    
    args = parser.parse_args()
    
    video_2_pic(
        video_path=args.input,
        interval=args.interval,
        crop_y1=args.crop_y1,
        crop_y2=args.crop_y2,
        output_dir=args.dir
    )


if __name__ == "__main__":
    main()
