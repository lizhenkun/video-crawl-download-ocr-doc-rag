#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取B站视频下载地址（支持mp4格式）
使用BilibiliPageCrawler类成员函数

用法:
    python download_video.py -u "BV15fXpBdE1d"
    python download_video.py -u "https://www.bilibili.com/video/BV15fXpBdE1d/"
    python download_video.py -u "BV15fXpBdE1d" -d
    python download_video.py -u "BV15fXpBdE1d" -d -o "D:\workspace\output"
"""
import os
import sys
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from libs import config, logger
from libs.bilibili_page_crawler import BilibiliPageCrawler
from libs.rename_video import replace_unsuitable_letter

from download_uper_videos import download_video


def download_a_video(url: str, output_dir: str, quality: int = 64):
    """获取并下载B站视频
    
    Args:
        url: B站视频URL或bvid
        quality: 视频清晰度 (192=1080P, 80=1080P, 64=720P)
        download: 是否下载视频
        output_dir: 输出目录
    """
    # 获取默认输出目录
    if not output_dir:
        logger.error("请指定输出目录")
        return False

    download_video(
        url, video_name="", output_dir=output_dir, 
        quality=quality, show_progress=True
    )

    # # Step 1: 提取bvid并获取视频信息
    # bvid = BilibiliPageCrawler.extract_bvid(url)
    # if not bvid:
    #     logger.error(f"无法从URL提取bvid: {url}")
    #     return

    # logger.info(f"获取视频信息: {bvid}")
    # video_info = BilibiliPageCrawler.get_video_info(bvid)
    # if not video_info:
    #     logger.error(f"无法获取视频信息: {bvid}")
    #     return

    # # Step 2: 获取下载URL (使用 BilibiliPageCrawler)
    # result = BilibiliPageCrawler.get_video_download_url(
    #     video_info, bvid, quality)

    # if not result:
    #     logger.error("无法获取下载链接")
    #     return
    
    # # # Step 3: 保存JSON (使用 BilibiliPageCrawler)
    # # from download_uper_videos import save_video_download_info
    # # save_video_download_info(result, output_dir)

    # # Step 4: 下载视频
    # if download:
    #     download_url = result.get("download_url", "")
    #     if not download_url:
    #         logger.error("下载链接为空")
    #         return
        
    #     # 清理标题作为文件名
    #     safe_title = replace_unsuitable_letter(result.get("title", "video"))
        
    #     # 确定文件扩展名
    #     ext = ".mp4" if ".mp4" in download_url else ".m4s"
    #     video_path = os.path.join(output_dir, f"{safe_title}_video{ext}")
        
    #     # 下载视频 (使用 BilibiliPageCrawler)
    #     success = BilibiliPageCrawler.download_video_file(download_url, video_path)
        
    #     if not success:
    #         logger.error("视频下载失败")
    #         return
        
    #     # 如果有音频，下载并合并
    #     audio_url = result.get("audio_url", "")
    #     if audio_url:
    #         audio_path = os.path.join(output_dir, f"{safe_title}_audio.m4s")
    #         audio_success = BilibiliPageCrawler.download_video_file(audio_url, audio_path)
            
    #         if audio_success:
    #             # 合并视频和音频
    #             final_path = os.path.join(output_dir, f"{safe_title}.mp4")
    #             merge_video_audio(video_path, audio_path, final_path)
    #             logger.success(f"下载完成: {final_path}")
    #             return
        
    #     logger.success(f"下载完成: {video_path}")
    # else:
    #     # 只显示下载链接
    #     logger.info(f"视频下载地址:\n{result.get('download_url', '')}")


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="获取B站视频下载地址(支持mp4)")
    parser.add_argument("-u", "--url", type=str, required=True, help="B站视频URL或bvid")
    parser.add_argument("-q", "--quality", type=int, default=64, help="视频清晰度: 192=1080P, 80=1080P, 64=720P (默认64)")
    parser.add_argument("-o", "--output", type=str, default=None, help="输出目录 (默认: 配置中的output_root)")
    
    args = parser.parse_args()

    output_dir = args.output or config.output_root
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"输入: {args.url}")
    logger.info(f"清晰度: {args.quality}")
    logger.info(f"输出目录: {args.output or config.output_root}")
    
    download_a_video(
        args.url, output_dir, args.quality
    )


if __name__ == "__main__":
    main()
