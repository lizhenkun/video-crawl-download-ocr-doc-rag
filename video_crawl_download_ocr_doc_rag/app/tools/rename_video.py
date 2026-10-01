# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
from datetime import datetime

from app.logger import logger


FILE_NAME_PATTERN_MAP = {
    '290663424': [
        # ~第918期~泰勒·斯威夫特公开表态支持哈里斯，特朗普时隔多年参加纽约911纪念活动，拜登“误”戴小红帽，美国大选悬念依旧，精彩依旧！20240912
        ('FILE_NAME_WITH_DATE_PATTERN', re.compile(r'第(\d+)期(.*)(\d{8})')),
        # ~第915期~教员的经济思想⑤实事求是与独立自主
        ('FILE_NAME_ONLY_PATTERN', re.compile(r'第(\d+)期(.*)')),
        # 《第七十二期》日元汇率有哪几个支撑点？.mp4
        ('FILE_NAME_WITH_PRE_DATE_PATTERN', re.compile(r'《第(\w+)期》(.*)')),
    ]
}

# ~第918期~泰勒·斯威夫特公开表态支持哈里斯，特朗普时隔多年参加纽约911纪念活动，拜登“误”戴小红帽，美国大选悬念依旧，精彩依旧！20240912
FILE_NAME_WITH_DATE_PATTERN = re.compile(r'第(\d+)期(.*)(\d{8})')
# ~第915期~教员的经济思想⑤实事求是与独立自主
FILE_NAME_ONLY_PATTERN = re.compile(r'第(\d+)期(.*)')
# 《第七十二期》日元汇率有哪几个支撑点？.mp4
FILE_NAME_WITH_PRE_DATE_PATTERN = re.compile(r'《第(\w+)期》(.*)')


def rename(row):
    # 如果已经存在 new_title , 返回
    if isinstance(row.new_title, str):
        if row.new_title:
            return row.new_title

    new_title = _rename(row, FILE_NAME_WITH_DATE_PATTERN)
    if new_title:
        return replace_unsuitable_letter(new_title)
    
    new_title = _rename(row, FILE_NAME_WITH_PRE_DATE_PATTERN)
    if new_title:
        return replace_unsuitable_letter(new_title)
    
    new_title = _rename(row, FILE_NAME_ONLY_PATTERN)
    if new_title:
        return replace_unsuitable_letter(new_title)
    
    date_str = row.created
    date_obj = datetime.fromtimestamp(row.created) 
    date_str = date_obj.strftime('%Y-%m-%d')

    return replace_unsuitable_letter(f'{date_str} {row.title}')


def replace_unsuitable_letter(title):
    """替代文件名不允许的字母"""
    # 文件名不允许带有字符 \/:*?"<>|
    replace_letters = {
        '\\': '#',
        '/': '#',
        ':': '：',
        '*': '@',
        '?': '？',
        '"': '“',
        '<': '《',
        '>': '》',
        '|': '#',
        '①': '1',
        '②': '2',
        '③': '3',
        '④': '4',
        '⑤': '5',
        '⑥': '6',
        '⑦': '7',
        '⑧': '8',
        '⑨': '9',
        '⑩': '10',
        '⑪': '11',
        '⑫': '12',
        '⑬': '13',
        '⑭': '14',
        '⑮': '15',
        '⑯': '16',
        '⑰': '17',
        '⑱': '18',
        '⑲': '19',
        '⑳': '20',
    }
    for k, v in replace_letters.items():
        title = title.replace(k, v)
    return title

def _rename(row, pattern):
    """ _rename """
    date_obj = datetime.fromtimestamp(row.created)
    date_format = date_obj.strftime('%Y-%m-%d')

    new_title = ''
    re_result = pattern.findall(row.title)
    if not re_result:
        return new_title
    
    re_result = re_result[0]
    logger.info(f'pattern {pattern}: {re_result}')

    if pattern in (FILE_NAME_WITH_DATE_PATTERN, FILE_NAME_ONLY_PATTERN):
        # _第745期~莫斯科遭数十年来最致命恐袭，ISIS宣布对此负责，此次事件对各方影响多大？后续会如何发展？20240323.mp4
        # ('745' ， 文件名 , '20240323')
        # ~第915期~教员的经济思想⑤实事求是与独立自主
        # ('915', 文件名)

        # 第N期
        no = re_result[0].zfill(5)
        # 文件名主题
        if len(re_result[1]) == 1:
            # continue
            new_title = row.title
        else:
            new_title = re_result[1] \
                .replace('_有何高见_免费在线阅读收听下载_-_喜马拉雅手机版', '') \
                .replace('_-_', '').replace('抖音', '').strip().replace(' ', '_')
            
            if new_title[0] in ['~', '-', '_']:
                new_title = new_title[1:]

            # 日期
            date_str = '_'
            if len(re_result) == 3:
                date_str = f'{re_result[2]}'
            else:
                date_str = f'{date_format}'

            if len(date_str) == 8:
                date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"

            new_title = f'{date_str} 第{no}期 {new_title}' 

    elif pattern == FILE_NAME_WITH_PRE_DATE_PATTERN:
        # 《第七十二期》日元汇率有哪几个支撑点？.mp4
        # ('七十二', '日元汇率有哪几个支撑点？.mp4')

        if len(re_result) == 2:
            no = chinese_to_arabic(re_result[0])
            no = str(no).zfill(3)
            new_title = f'{date_format} {no} {re_result[1]}'
    
    logger.info(f'{row.title} , new: {new_title}')
    
    return new_title


def chinese_to_arabic(chinese_num_str):  
    """
    print(chinese_to_arabic("七十三"))          # 应输出 73  
    print(chinese_to_arabic("一百"))            # 应输出 100  
    print(chinese_to_arabic("一百〇一"))        # 应输出 101  
    print(chinese_to_arabic("一百〇九"))        # 应输出 109
    print(chinese_to_arabic("一百一十"))        # 应输出 110
    print(chinese_to_arabic("一百十一"))        # 应输出 111
    print(chinese_to_arabic("一百十九"))        # 应输出 119
    print(chinese_to_arabic("一百二十"))        # 应输出 120
    print(chinese_to_arabic("一百二一"))        # 应输出 121
    """
    # 数字映射  
    num_map = {
        '〇': 0, '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,  '五': 5, 
        '六': 6, '七': 7, '八': 8, '九': 9,
    }
    unit_map = {
         '十': 10, '百': 100
    }
    # 单位映射及其对应的乘数，注意万是10000  
    
    _tmp_num = ''
    total_num = 0

    for char in chinese_num_str:
        if char in num_map:
            arabic = num_map[char]
            _tmp_num += str(arabic)
        elif char in unit_map:
            unit_num = unit_map[char]
            if not _tmp_num:
                _tmp_num = 1

            int_num = int(_tmp_num) * unit_num
            # print(f'{chinese_num_str} - {char} - {int_num}')
            total_num += int_num

            _tmp_num = ''
    
    if _tmp_num:
        total_num += int(_tmp_num)

    print(f'input : {chinese_num_str} , output: {total_num}')
  
    return total_num
