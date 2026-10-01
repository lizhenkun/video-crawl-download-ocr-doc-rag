# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File: 03_batch_download_by_excel.py
Authors: 坤叔(1292746975@qq.com)
Date: 2024-10-03

python -m video_crawl_download_ocr_doc_rag.app.crawl_bilibili.03_batch_download_by_excel
"""
import os
import json
import pandas
import subprocess
from urllib.parse import urlparse, parse_qs 

from app.config import config
from app.logger import logger

BILIBILI_KEY = "https://www.bilibili.com"
LEMONDL_KEY = "https://lemondl.com/"


def download_all():
    """下载所有配置的up主 在Excel中未下载且需要下载的视频"""
    for uploader_id, uper_info in config.bilibili_up_info.items():
        uper_info["id"] = uploader_id
        download_up_videos(uper_info)


def download_up_videos(uper_info):
    """download_videos_from_excel"""
    uploader = uper_info["uploader"]
    output_dir = os.path.join(config.output_root, uploader)
    excel_file = os.path.join(config.output_root, f"{uploader}.xlsx")

    print(f"开始下载UP主：{uploader}")
    download_videos_from_excel(output_dir, excel_file)

def download_videos_from_excel(output_dir, excel_file):
    """download_videos_from_excel"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    df = pandas.read_excel(excel_file)
    if "download_url" not in df.columns:
        df["download_url"] = ""
    if "output_file" not in df.columns:
        df["output_file"] = ""

    for index, row in df.iterrows():
        title = row.new_title
        if not title:
            title = row.title

        if not isinstance(row.lemonUrl, str):
            continue

        download_url = row.lemonUrl.strip()
        
        if download_url[:len(LEMONDL_KEY)] == LEMONDL_KEY:
            parsed_url = urlparse(download_url)
            query_params = parsed_url.query
            params = parse_qs(query_params)
            # logger.info(params)

            params = json.loads(params["data"][0])
            bvid = params["bvid"]
            
            if "bvid" in row:
                if row.bvid != bvid:
                    logger.info(f"{bvid}, {row.bvid == bvid}")
                    df.loc[index, "bvid_error"] = "是"
                    continue
            
            if isinstance(row.output_file, str) and row.output_file:
                # 有值代表已经下载过了
                continue

            download_url = params["url"]

            output_file = download_video(download_url, title, output_dir)

            logger.info(
                f"\ntitle: {title}"
                f"\ndownload_url: {download_url}"
                f"\noutput_file: {output_file}"
            )
            # 保证 download_url 是 string 类型
            df[["download_url", "output_file"]] = df[["download_url", "output_file"]].astype(str)

            df.loc[index, "download_url"] = download_url
            df.loc[index, "output_file"] = output_file

    for i in range(3):
        try:
            df.to_excel(excel_file, index=False)
            logger.info(f"保存成功 : {excel_file}")
        except:
            if i == 0:
                input(f"EXCEL {excel_file} 写入失败, 请关闭Excel, 然后按回车键继续...")
            else:
                raise
    return

def download_video(download_url, title, output_dir):
    """download video"""
    parts = download_url.split("?")
    file_type = parts[0].strip().rsplit(".", 1)[-1]
    
    if not file_type:
        file_type = "mp4"

    output_file = os.path.join(output_dir, f"{title}.{file_type}")
    logger.info(f"output_file: {output_file}")

    if os.path.exists(output_file):
        logger.info(f"文件已存在: {output_file}")
        return output_file

    rm_cmd = f"rm -rf '{output_file}'" # Linux/MacOS
    if os.name == "nt": # windows
        rm_cmd = f"del '{output_file}'"

    cmd = (
        # -o "{output_file}.log" 
        f'wget "{download_url}" -o "wget.log" -O "{output_file}"  && echo "Success")'
        f'|| (echo "Wget failed, delete file: {output_file}" && {rm_cmd})'
    )
    logger.info(f"下载文件， 通过命令: {cmd}")
    
    p = subprocess.run(cmd, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
    
    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        return output_file
    
    return ""

if __name__ == "__main__":
    download_all()