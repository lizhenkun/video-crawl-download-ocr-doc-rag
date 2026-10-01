# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authors: 坤叔(1292746975@qq.com)
"""
import os

from app.tools.rename_video import replace_unsuitable_letter

from app.config import config
from app.logger import logger, print_caller_stack
from app.tools.download_videos_from_excel import download_videos_from_excel

def download_collection_videos(excel_path):
    """
    """
    output_dir = os.path.dirname(excel_path)
    logger.info(f"downloading videos from {os.path.basename(excel_path)} to {output_dir}")

    download_videos_from_excel(output_dir=output_dir, excel_file=excel_path)


if __name__ == '__main__':
    # python -m app.tools.download_collection_videos
    excel_path = "D:/workspace/video-crawl-download-ocr-doc-rag/video_crawl_download_ocr_doc_rag/output/【公开课】温铁军：中国经济研究（33讲）/【公开课】温铁军：中国经济研究（33讲）.xlsx"
    
    download_collection_videos(excel_path)