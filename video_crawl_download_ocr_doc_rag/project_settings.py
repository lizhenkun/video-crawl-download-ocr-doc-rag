# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authors: 坤叔(1292746975@qq.com)
"""
import os
import re


class ProjectSettings(object):
    # 如果这样定义, 子类在另一个目录下， 那么 子类.PRJ_DIR 时, PRJ_DIR 会变成 子类所在的目录, 
    # 而非当前文件所在的目录, 会导致目录不符合预期
    # PRJ_DIR = os.path.abspath('.') 
    PRJ_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = os.path.join(PRJ_DIR, 'output')

    VIDOE_DIR = os.path.join(PRJ_DIR, 'video')
    DOC_DIR = os.path.join(PRJ_DIR, 'doc')

    @classmethod
    def test(cls):
        print(
            f"PRJ_DIR: {cls.PRJ_DIR}"
            f"\nOUTPUT_DIR: {cls.OUTPUT_DIR}"
        )
        
        print('\n1: \n.')
        print(os.path.abspath('.'))
        print(os.path.dirname(os.path.abspath('.')))

        print(f'\n2: \n{os.path.pardir}')
        print(os.path.abspath(os.path.pardir))
        print(os.path.dirname(os.path.abspath('.')))

        print(f'\n3: \n{__file__}')
        print(os.path.abspath(__file__))
        print(os.path.dirname(os.path.abspath(__file__)))
        
        print(f'\n4: PRJ_DIR and OUTPUT_DIR')
        print(cls.PRJ_DIR)
        print(cls.OUTPUT_DIR)

if __name__ == '__main__':
    ProjectSettings.test()