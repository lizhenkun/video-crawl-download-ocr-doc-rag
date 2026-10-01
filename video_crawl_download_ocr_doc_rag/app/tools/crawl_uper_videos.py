# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authors: 坤叔(1292746975@qq.com)
获取 up主的视频列表并保存(更新)到 Excel里 ( resources/up主名.xlsx )

python -m app.tools.crawl_uper_videos.py
"""
import os
import time

import pandas
from pandas import DataFrame

from app.libs import BilibiliPageCrawler
from app.tools.rename_video import rename

from app.config import config
from app.logger import logger, print_caller_stack


def crawl_all():
    """抓取所有配置的up主的视频列表"""
    crawler = BilibiliPageCrawler()

    for uploader_id, uper_info in config.bilibili_up_info.items():
        uper_info['id'] = uploader_id
        all_video_list = crawl_uper_videos(crawler, uper_info)
        logger.info(f'{uploader_id}: \n{all_video_list}')

        output_excel_file = save_videos_2_excel(uper_info, all_video_list)
        logger.debug(f'Excel: {output_excel_file}')

    crawler.driver.quit()
    return


def crawl_uper_videos(crawler: BilibiliPageCrawler, uper_info):
    """ 抓取 某个 up主的视频列表"""
    uploader = uper_info['uploader']
    logger.info(f'Begin uploader: {uploader}')

    all_video_list = []

    special_types = uper_info.get('special_types', [''])

    for special_type in special_types:
        page_count = uper_info.get('page_count', 1)
        space_page_resp = crawler.crawl_space_page(
            uploader_id=uper_info['id'], 
            page_count=page_count, 
            special_type=special_type
        )

        space_page_resp.data['uploader'] = uploader
        logger.info(f'space_page_resp: {space_page_resp.response}')

        video_list = space_page_resp.data['video_list']
        print(f'结束爬虫, 看看有多少数据: {len(video_list)}')
        all_video_list.extend(video_list)
        time.sleep(4)

    return all_video_list


def save_videos_2_excel(uper_info, video_list):
    """ 保存视频列表到 Excel文件中"""
    output_dir = config.output_root
    uploader = uper_info["uploader"]

    __OUTPUT_EXCEL = os.path.join(output_dir, f'{uploader}.xlsx')
    __OUTPUT_CSV = os.path.join(output_dir, f'{uploader}.csv')

    total_df = DataFrame(video_list)
    if os.path.exists(__OUTPUT_EXCEL):
        df = total_df
        total_df = DataFrame()
        
        old_df = pandas.read_excel(__OUTPUT_EXCEL)
        logger.info(f'old_df : {old_df.shape} , columns : {old_df.columns}')
        logger.info(f'new_df : {df.shape} , columns : {df.columns}')

        new_df = df[~df.bvid.isin(old_df.bvid)]
        total_df = pandas.concat([new_df, old_df], ignore_index=True)
        total_df = total_df.drop_duplicates(subset=['bvid'], keep='first')
    else:
        total_df['new_title'] = ''
        total_df['lemonUrl'] = ''
        total_df['download_url'] = ''
        total_df['output_file'] = ''
        total_df['bvid_error'] = ''
        total_df['星级'] = ''
        total_df['分类'] = ''
        total_df['转文字'] = ''

    total_df['new_title'] = total_df.apply(rename, axis=1)

    total_df.sort_values(by='created', ascending=False, inplace=True) 
    logger.info(f'output total_df : {total_df.shape}')

    for i in range(3):
        try:
            total_df.to_excel(__OUTPUT_EXCEL, index=False)
            logger.info(f'OUTPUT TO EXCEL SUCCESS: {__OUTPUT_EXCEL}')
            break
        except:
            logger.error(f'{__OUTPUT_EXCEL} 保存失败 , 请关闭文件后再试')
            if i == 0:
                input("按任意键继续重试...")
                    
    total_df[['title']].to_csv(__OUTPUT_CSV, index=False)

    return __OUTPUT_EXCEL


if __name__ == '__main__':
    # python -m app.tools.update_uper_list
    crawl_all()