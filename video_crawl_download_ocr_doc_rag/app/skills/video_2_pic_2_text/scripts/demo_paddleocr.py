# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PaddleOCR 测试脚本

使用方法:
    python demo_paddleocr.py -p "图片路径.jpg"
"""
import argparse
from datetime import datetime
from paddleocr import PaddleOCR

import paddle
paddle.set_device('cpu')

import os
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

ocr = PaddleOCR(
    ocr_version="PP-OCRv4",
    precision='fp16',

    # use_doc_orientation_classify=False, # 通过 use_doc_orientation_classify 参数指定不使用文档方向分类模型
    # use_doc_unwarping=False, # 通过 use_doc_unwarping 参数指定不使用文本图像矫正模型
    # use_textline_orientation=False, # 通过 use_textline_orientation 参数指定不使用文本行方向分类模型
)

# 强制使用CPU，避免GPU相关警告
# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

def main():
    parser = argparse.ArgumentParser(description="PaddleOCR 测试")
    parser.add_argument("-p", "--path", required=False, help="输入图片路径")
    args = parser.parse_args()
    
    # 初始化OCR - 默认使用 PP-OCRv5 模型
    # ocr = PaddleOCR(
    #     # ocr_version="PP-OCRv4", # 默认使用 PP-OCRv5 模型
    #     # text_detection_model_name="PP-OCRv5_mobile_det",
    #     # text_recognition_model_name="PP-OCRv5_mobile_rec",
    #     # use_textline_orientation=False,
    #     use_doc_orientation_classify=False,
    #     use_doc_unwarping=False,
    #     use_textline_orientation=False,
    #     lang='ch',
    #     # use_angle_cls=False, 
    #     # use_gpu=False
    #     device="cpu"
    # )
    
        
    img_path = args.path
    if not img_path:
        img_path = "./test.png"
    
    now = datetime.now()
    print(f"正在识别图片: {img_path}")
    
    result = ocr.predict(img_path)
    for index, item in enumerate(result):
        print(index)
        print(item["rec_texts"])
        print(item["rec_scores"])
        # print()
        # print(type(res))
        # print()
        # print()
    end = datetime.now()
    print(f"耗时: {end - now}")
    
    # if result and result[0]:
    #     print(f"\n识别到 {len(result[0])} 条文本:\n")
    #     for line in result[0]:
    #         text = line[1][0]
    #         confidence = line[1][1]
    #         print(f"识别文本: {text}, 置信度: {confidence:.2f}")
    # else:
    #     print("未识别到文字")


if __name__ == "__main__":
    main()
