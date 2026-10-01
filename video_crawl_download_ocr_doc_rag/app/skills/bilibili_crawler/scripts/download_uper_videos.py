#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载UP主视频脚本
从Excel读取bvUrl，使用BilibiliPageCrawler下载

用法:
    python download_uper_videos.py
"""
import os
import time
import json
import pandas
import traceback
from pandas import DataFrame

import sys
from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from libs import config, logger
from libs.bilibili_page_crawler import BilibiliPageCrawler
from libs.rename_video import replace_unsuitable_letter


def download_all():
    """下载所有配置的UP主的视频"""
    for uploader_id, uper_info in config.bilibili_up_list.items():
        uploader = uper_info.get("uploader", uploader_id)  # 获取UP主名称，若无则使用ID
        logger.info(f"开始处理UP主: {uploader}")  # 记录处理进度
        download_up_videos(uploader)  # 下载该UP主的视频


def download_up_videos(uploader: str):
    """下载某个UP主的视频"""
    excel_file = os.path.join(config.output_root, f"{uploader}.xlsx")
    
    if not os.path.exists(excel_file):
        logger.warning(f"Excel文件不存在: {excel_file}")
        return
    
    logger.info(f"读取Excel: {excel_file}")
    df = pandas.read_excel(excel_file)
    
    # 确保必要的列存在
    if "bvUrl" not in df.columns:
        logger.warning(f"Excel中无 bvUrl 列，跳过: {uploader}")
        return
    
    if "output_file" not in df.columns:
        df["output_file"] = ""
    
    if "download_url" not in df.columns:
        df["download_url"] = ""
    
    download_count = 0
    skip_count = 0
    
    for index, row in df.iterrows():
        bv_url = row.get("bvUrl", "")
        
        # 检查：bvUrl 不为空 且 output_file 为空
        if not bv_url or not isinstance(bv_url, str):
            logger.info(f"bvUrl 为空 , 跳过")
            continue
        
        if isinstance(row.get("output_file", ""), str) and row.get("output_file", "").strip():
            skip_count += 1
            continue

        # 输出目录
        output_dir = os.path.join(config.output_root, uploader)
        os.makedirs(output_dir, exist_ok=True)

        # 如果文件已经存在，则跳过
        output_file = os.path.join(output_dir, f"{row.new_title}.mp4")
        if os.path.exists(output_file):
            df.loc[index, "output_file"] = output_file
            logger.info(f"已存在: {output_file}")
            skip_count += 1
            continue
        
        # 提取bvid
        bvid = BilibiliPageCrawler.extract_bvid(bv_url)
        if not bvid:
            logger.warning(f"无法从URL提取bvid: {bv_url}")
            continue
        
        # 获取标题
        title = row.get("new_title", "")
        if not title:
            title = row.get("title", "未知标题")
        
        # 调用BilibiliPageCrawler获取下载链接并下载
        logger.info(f"开始下载: {title} ({bvid})")
        
        try:
            result = download_row(row, output_dir)
            
            if result:
                df.loc[index, "output_file"] = result
                download_count += 1
                logger.success(f"下载成功: {result}")
            else:
                logger.error(f"下载失败(Excel会备注: DOWNLOAD FAIL): {title}")
                df.loc[index, "output_file"] = "DOWNLOAD FAIL"
        except Exception as e:
            logger.error(f"下载异常(Excel会备注: DOWNLOAD FAIL): \n{traceback.format_exc()}")
            df.loc[index, "output_file"] = "DOWNLOAD FAIL"
        
        # 避免请求过快
        time.sleep(2)
    
    logger.info(f"处理完成: {uploader}, 下载: {download_count}, 跳过: {skip_count}")
    
    # 保存Excel
    save_excel(df, excel_file)


def download_row(row, output_dir: str, quality: int = 64) -> str:
    """使用BilibiliPageCrawler下载视频
    
    Args:
        row: Excel行数据
        output_dir: 输出目录
        quality: 视频清晰度
        
    Returns:
        下载后的文件路径
    """
    video_name = replace_unsuitable_letter(row.new_title)
    logger.info(f"处理 {row.bvUrl} : {video_name}")
    return download_video(row.bvUrl, video_name, output_dir, quality, show_progress=True)


def download_video(
    bv_url, video_name, output_dir, quality: int=64, show_progress: bool=False):
    """
    Args:
        bv_url: B站视频URL或bvid , eg. https://www.bilibili.com/video/BV17NrWBaEka/
        video_name: 视频名称
        output_dir: 输出目录
        quality: 视频清晰度
    """
    # Step 1: 获取下载URL
    result = BilibiliPageCrawler.get_video_download_url(bv_url, quality)
    if not result:
        logger.error(f"无法获取下载视频: {bv_url}")
        return ""
    
    # logger.info(f"result: {result}")

    if not video_name:
        video_name = result.get("title", result["bvid"])
        video_name = replace_unsuitable_letter(video_name)

    download_url = result.get("download_url", "")
    if not download_url:
        logger.error(f"下载链接为空: {bv_url}")
        return ""
    
    # 确定文件扩展名
    ext = ".mp4" if ".mp4" in download_url else ".m4s"
    video_path = os.path.join(output_dir, f"{video_name}{ext}")

    logger.info(f"\n下载地址: {download_url}\n输出地址: {video_path}\n")

    if os.path.exists(video_path):
        logger.info(f"已存在: {video_path}")
        return video_path
    
    # Step 2: 保存JSON
    # save_video_download_info(result, output_dir)

    # Step 3: 下载视频
    success = BilibiliPageCrawler.download_video_file(
        download_url, video_path, show_progress)
    if not success:
        logger.error(f"视频下载失败: {bv_url}")
        return ""
    
    # # Step 4: 如果有音频，下载并合并
    # audio_url = result.get("audio_url", "")
    # if audio_url:
    #     audio_path = os.path.join(output_dir, f"{video_name}_audio.m4s")
    #     audio_success = BilibiliPageCrawler.download_video_file(audio_url, audio_path)
        
    #     if audio_success:
    #         # 合并视频和音频
    #         final_path = os.path.join(output_dir, f"{video_name}.mp4")
    #         merge_video_audio(video_path, audio_path, final_path)
    #         return final_path
    
    return video_path


def merge_video_audio(video_path: str, audio_path: str, output_path: str):
    """合并视频和音频
    
    Args:
        video_path: 视频文件路径
        audio_path: 音频文件路径
        output_path: 输出文件路径
    """
    import subprocess
    
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-i", audio_path,
        "-c", "copy",
        "-y",  # 覆盖已存在的文件
        output_path
    ]
    
    try:
        logger.info(f"合并视频和音频: {output_path}")
        subprocess.run(cmd, check=True, capture_output=True)
        
        # 删除分离的文件
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        logger.success(f"合并成功: {output_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"合并失败: {e}")
    except FileNotFoundError:
        logger.warning("ffmpeg未安装，保留分离的视频和音频文件")


def save_excel(df: DataFrame, excel_file: str):
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


def save_video_download_info(result: dict, output_dir: str = "output") -> str:
    """保存下载信息到JSON文件
    
    Args:
        result: get_video_download_url 返回的字典
        output_dir: 输出目录
        
    Returns:
        JSON文件路径
    """
    bvid = result.get("bvid", "unknown")
    json_file = os.path.join(output_dir, f"{bvid}.json")
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    logger.success(f"JSON已保存: {json_file}")
    return json_file


if __name__ == "__main__":
    download_all()
