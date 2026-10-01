# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authors: 坤叔(1292746975@qq.com)
参考:
DrissionPage的使用
https://baijiahao.baidu.com/s?id=1801556183340018772&wfr=spider&for=pc

python bilibili_up_crawler_by_drission_page.py
"""
import os
import re
import json
import time
import subprocess
from datetime import datetime
import traceback
from urllib.parse import urlparse, parse_qs

import pandas
from pandas import DataFrame
from DrissionPage import ChromiumPage, ChromiumOptions

from app.config import config
from app.logger import logger
from app.libs import StdResponse


LEMONDL_KEY = 'https://lemondl.com/'


class BilibiliPageCrawler(object):
    """
    bilibili 页面爬虫器
    """
    @classmethod
    def create_webdriver(cls):
        """
        create_webdriver
        """
        driver = ChromiumPage(config.CHROMIUM_OPTIONS)
        return driver

    def __init__(self, driver: ChromiumPage = None):
        """
        """
        if not driver:
            driver = self.create_webdriver()
        self.driver = driver

    def crawl_space_page(self, uploader_id, page_count=1, special_type=''):
        """
        https://space.bilibili.com/290663424/upload/video

        Space Url = f'https://space.bilibili.com/{uploader_id}/video'
        """
        std_resp = StdResponse()

        # 最新发布: space_url = f'https://space.bilibili.com/{uploader_id}/video?tid=0&special_type=&pn={pn}&keyword=&order=pubdate'
        # 充电专属: space_url = f'https://space.bilibili.com/{uploader_id}/video?tid=0&special_type=charging&pn={pn}&keyword=&order=pubdate'
        # space_url eg. https://space.bilibili.com/290663424/video?tid=0&special_type=&pn=2&keyword=&order=pubdate
        # 已经被 B站屏蔽了
        # space_url = f'https://space.bilibili.com/{uploader_id}/video?tid=0&special_type={special_type}&pn={pn}&keyword=&order=pubdate'
        # https://space.bilibili.com/290663424/upload/video
        space_url = f'https://space.bilibili.com/{uploader_id}/upload/video'
        logger.info(f'space_url: {space_url}')

        web_driver = self.driver
        # search_url_pattern = f'https://api.bilibili.com/x/space/wbi/arc/search?mid={uploader_id}'
        search_url_pattern = f'https://api.bilibili.com/x/space/wbi/arc/search'
        
        logger.info('crawling...')

        web_driver.listen.start(search_url_pattern) # 开始监听，指定获取包含该文本的数据包(部分url)
        web_driver.get(space_url)
        
        total_video_list = []

        cur_pn = 0
        while page_count < 0 or cur_pn < page_count:
            cur_pn += 1
            
            # web_driver.wait.load_start()

            video_list = []
            for retry in range(5):
                try:
                    # res 是拦截到的接口的响应体
                    res = web_driver.listen.wait()

                    # res.response.body: dict
                    video_list = self.get_video_info_list(res.response.body)
                    print(
                        f'当前页 {cur_pn}'
                        f'\n本页视频数量: {len(video_list)}'
                        f'\n第一个视频: {video_list[0]['title']}'
                        f'\n监听的url: {res.url}'
                        f'\nheaders: {res.response.headers}'
                    )
                    break
                except Exception as e:
                    print(f'第 {retry + 1} 次抓取失败: {e}')
                    if retry < 4:
                        print('尝试刷新页面...')
                        web_driver.get(space_url)
                        web_driver.listen.start(search_url_pattern)
                        time.sleep(2)
                    else:
                        print('已达到最大重试次数 (5次)')

            if video_list:
                total_video_list.extend(video_list)

            time.sleep(3)
            try:
                # web_driver: ChromiumPage
                # btn: DrissionPage._elements.chromium_element
                # from DrissionPage._elements.chromium_element import ChromiumElement
                btn = web_driver('下一页')
                # print(btn , {btn.html})
                # help(btn)
                # AttributeError: 'ChromiumElement' object has no attribute 'exists'
                if btn.states.has_rect:
                    # input('回车 ， 自动点击下一页')
                    btn.click()
                    continue
                else:
                    print('没有下一页了 , break')
                    break
            except:
                print('没有下一页了 , break')
                break

        std_resp.data['uploader_id'] = uploader_id
        std_resp.data['space_url'] = space_url
        std_resp.data['search_url'] = res.url
        std_resp.data['pn'] = cur_pn
        std_resp.data['video_list'] = total_video_list

        return std_resp

    @classmethod
    def get_video_info_list(cls, ajax_data):
        """
        get video info list
        """
        # write to json for test
        # with open(f'{uploader_id}_response.json', mode='w', encoding='utf-8') as writer:
        #     json.dump(ajax_data, writer)

        # test
        # with open(f'{uploader_id}_response.json', mode='r', encoding='utf-8') as reader:
        #     ajax_data = json.load(reader)

        vlist = ajax_data['data']['list']['vlist']
        logger.info(f'vlist len: {len(vlist)}')

        new_list = []
        for v_info in vlist:
            bvid = v_info['bvid']
            v_item = {
                'title': v_info['title'],
                'created': v_info['created'], # 创建时间
                'bvid': bvid, # video id
                'bvUrl': f'https://www.bilibili.com/video/{bvid}/',
                'description':v_info['description']
            }
            new_list.append(v_item)
        
        return new_list

    @classmethod
    def download_videos(cls, space_page_resp):
        """
        download videos
        """
        output_dir = space_page_resp.get('output', 'output')
        uploader = space_page_resp['uploader']
        excel_file = os.path.join(output_dir, f'{uploader}.xlsx')

        df = pandas.read_excel(excel_file)

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
                # print(params)

                params = json.loads(params['data'][0])
                bvid = params['bvid']
                
                if row.bvid != bvid:
                    logger.warning(f'row: {bvid} , {row.bvid == bvid}')
                    df.loc[index, 'bvid_error'] = '是'
                    continue

                download_url = params['url']

                output_file = download_file(output_dir, download_url, title)
                df.loc[index, 'download_url'] = download_url
                df.loc[index, 'output_file'] = output_file

        df.to_excel(excel_file, index=False)




def download_file(output_dir, download_url, title):
    """
    download
    """
    parts = download_url.split('?')
    file_type = parts[0].strip().rsplit('.', 1)[-1]
    print(f'download file type: {file_type}')
    if not file_type:
        file_type = 'mp4'

    target = f'{output_dir}/{title}.{file_type}'
    if os.path.exists(target):
        return target

    cmd = f'wget "{download_url}" -O "{target}"'
    print(cmd)
    p = subprocess.run(cmd, shell=True)
    return target

if __name__ == '__main__':
    # python -m video_crawl_download_ocr_doc_rag.app.crawl_bilibili.bilibili_up_crawler_by_drission_page
    driver = BilibiliPageCrawler.create_webdriver()
    crawler = BilibiliPageCrawler(driver)
    
    for uploader_id, item in config.bilibili_up_info.items():
        logger.info(f'Begin uploader: {item}')
        uploader = item['uploader']
        # uploader_id = 701978895
        all_video_list = []
        excel = ''
        
        # special_type_list = ['', 'charging']
        special_type_list = ['']
        for special_type in special_type_list:
            # pn = -1 # 抓全部
            # pn = 4 # 抓4页
            pn = 1
            space_page_resp = crawler.crawl_space_page(uploader_id=uploader_id, page_count=pn, special_type=special_type)

            space_page_resp.data['uploader'] = uploader
            logger.info(f'space_page_resp: {space_page_resp.response}')
            # input('\n按回车键继续...')

            video_list = space_page_resp.data['video_list']
            print(f'结束爬虫, 看看有多少数据: {len(video_list)}')
            all_video_list.extend(video_list)
            time.sleep(4)

        if all_video_list:
            output_excel_file = crawler.save_video_list_2_excel(
                space_page_resp.data['uploader'], 
                all_video_list, 
            )
            logger.debug(f'Excel: {output_excel_file}')
            crawler.rename_title(output_excel_file)

    # 关闭浏览器
    driver.quit()
