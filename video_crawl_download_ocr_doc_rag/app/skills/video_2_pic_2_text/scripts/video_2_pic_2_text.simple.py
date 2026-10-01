#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频转图片再转文字 - 批量处理UP主视频
读取 config.toml 里的 up主列表，遍历每个UP主的Excel，处理未转文字的视频
"""
import os
import sys
import time
import traceback
from pathlib import Path

import pandas as pd

# 添加项目根目录到路径
SCRIPT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from libs import config, logger
from video_2_pic import video_2_pic
from pic_2_text import pic_2_text


def process_all_upers():
    """处理所有配置的UP主"""
    up_list = config.bilibili_up_list
    
    logger.info(f"开始处理 {len(up_list)} 个UP主")
    
    for uploader_id, up_info in up_list.items():
        uploader = up_info.get("uploader", uploader_id)
        logger.info(f"\n{'='*50}")
        logger.info(f"开始处理UP主: {uploader} (ID: {uploader_id})")
        logger.info(f"{'='*50}")
        
        try:
            process_up_video(uploader_id, uploader)
        except Exception as e:
            logger.error(f"处理UP主失败: {uploader}, 错误: {e}")
            logger.error(traceback.format_exc())
        
        # 避免请求过快
        time.sleep(1)
    
    logger.info("\n所有UP主处理完成!")


def process_up_video(uploader_id: str, uploader: str):
    """处理某个UP主的视频
    
    Args:
        uploader_id: UP主ID
        uploader: UP主名称
    """
    # 获取UP主配置
    up_config = config.get_up_config(uploader_id)
    
    # Excel路径
    excel_file = os.path.join(config.excel_root, f"{uploader}.xlsx")
    
    if not os.path.exists(excel_file):
        logger.warning(f"Excel文件不存在: {excel_file}")
        return
    
    logger.info(f"读取Excel: {excel_file}")
    df = pd.read_excel(excel_file)
    
    # 确保必要的列存在
    if "output_file" not in df.columns:
        df["output_file"] = ""
    
    # 转文字列名可能是 "转文字" 或 "text" 或其他，需要检查
    text_col = None
    for col in df.columns:
        if "转文字" in col or "text" in col.lower():
            text_col = col
            break
    
    if text_col is None:
        # 添加新列
        text_col = "转文字"
        df[text_col] = ""
    
    # 获取UP主特定的配置参数
    interval = up_config.get("interval", config.video_interval)
    crop_y1 = up_config.get("crop_y1", config.crop_y1)
    crop_y2 = up_config.get("crop_y2", config.crop_y2)
    
    # 检查是否有 cropped_kwargs
    cropped_kwargs = up_config.get("cropped_kwargs", {})
    if cropped_kwargs:
        crop_y1 = cropped_kwargs.get("y1", crop_y1)
        crop_y2 = cropped_kwargs.get("y2", crop_y2)
    
    logger.info(f"配置: interval={interval}, crop_y1={crop_y1}, crop_y2={crop_y2}")
    
    process_count = 0
    skip_count = 0
    
    for index, row in df.iterrows():
        # 检查: 转文字列不为空 -> 跳过
        text_value = row.get(text_col, "")
        if text_value and isinstance(text_value, str) and text_value.strip():
            skip_count += 1
            logger.info(f"[{index}] 转文字已存在, 跳过")
            continue
        
        # 检查: output_file 不存在 -> 跳过
        output_file = row.get("output_file", "")
        if not output_file or not isinstance(output_file, str):
            skip_count += 1
            logger.info(f"[{index}] output_file为空, 跳过")
            continue
        
        if not os.path.exists(output_file):
            skip_count += 1
            logger.info(f"[{index}] 文件不存在: {output_file}, 跳过")
            continue
        
        # 获取视频标题
        title = row.get("new_title", "")
        if not title:
            title = row.get("title", f"video_{index}")
        
        logger.info(f"\n[{index}] 开始处理: {title}")
        logger.info(f"    视频路径: {output_file}")
        
        try:
            # 视频转图片
            pic_dir = video_2_pic(
                video_path=output_file,
                interval=interval,
                crop_y1=crop_y1,
                crop_y2=crop_y2,
                output_dir=None  # 使用默认输出目录（视频同目录）
            )
            
            # 图片转文字
            text_file = pic_2_text(pic_dir=pic_dir)
            
            # 更新DataFrame
            df.at[index, text_col] = "DONE"
            
            process_count += 1
            logger.success(f"[{index}] 处理完成!")
            
        except Exception as e:
            logger.error(f"[{index}] 处理失败: {e}")
            logger.error(traceback.format_exc())
            df.at[index, text_col] = f"FAIL: {str(e)}"
        
        # 避免过快
        time.sleep(1)
    
    logger.info(f"处理完成: {uploader}, 处理: {process_count}, 跳过: {skip_count}")
    
    # 保存Excel
    save_excel(df, excel_file)


def save_excel(df: pd.DataFrame, excel_file: str):
    """保存Excel文件"""
    for i in range(3):
        try:
            df.to_excel(excel_file, index=False)
            logger.success(f"Excel已保存: {excel_file}")
            return
        except Exception as e:
            if i == 0:
                input(f"Excel {excel_file} 写入失败, 请关闭Excel, 按回车继续...")
            else:
                logger.error(f"保存失败: {e}")
                raise


def main():
    process_all_upers()


if __name__ == "__main__":
    main()
