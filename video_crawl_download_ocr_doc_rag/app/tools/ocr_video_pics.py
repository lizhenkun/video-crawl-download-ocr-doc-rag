# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
识别 视频对应图片里的 文字

paddleocr text_recognition -i D:\workspace\video-crawl-download-ocr-doc-rag\output\有何高见9527\2026-01-14 595 特朗普2025年经济政策如何影响世界经济？\00500.png

# 默认使用 PP-OCRv5 模型
paddleocr ocr -i D:\\general_ocr_002.png --use_doc_orientation_classify False --use_doc_unwarping False --use_textline_orientation False \
    --save_path ./output \
    --device gpu:0 

# 通过 --ocr_version 指定 PP-OCR 其他版本
paddleocr ocr -i ./general_ocr_002.png --ocr_version PP-OCRv4
"""
import os
import traceback
import pandas
from pathlib import Path

from paddleocr import PaddleOCR
from paddleocr import TextRecognition

from app.config import config
from app.logger import logger

# GLOBAL_OCR = PaddleOCR()
# GLOBAL_OCR = PaddleOCR() # 文本检测+文本识别
GLOBAL_OCR = TextRecognition()
GLOBAL_OCR = TextRecognition(model_name="PP-OCRv5_server_rec")

def ocr_pictures(pic_dir, csv_file):
    """识别 图片里的文字"""
    img_path = ""
    result = GLOBAL_OCR.predict(img_path)


def _test():
    # video_file_path = Path("D:\\") / "demo" / "2026-01-14 595 特朗普2025年经济政策如何影响世界经济？.mp4"
    img_path = "D:/02.png"
    print('-' * 100)
    print(img_path)
    if os.path.exists(img_path):
        output = GLOBAL_OCR.predict(img_path)
        for res in output:
            res.print()
            # print(res)
    else:
        print("文件不存在")
    # ocr_pictures(video_file_path)


if __name__ == '__main__':
    # python -m app.tools.ocr_video_pics
    _test()
    # ocr_pictures()