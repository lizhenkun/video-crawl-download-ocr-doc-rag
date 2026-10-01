# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authors: 坤叔(1292746975@qq.com)
参考:
https://blog.csdn.net/qq_39147299/article/details/132236245
"""
import json
from pydantic import BaseModel, Field
from typing import Union, List, Dict


class StdResponse(BaseModel):
    """
    StdResponse
    """
    status: int = Field(0, description='状态码')
    msg: str = Field('', description='消息')
    data: Union[Dict, List] = Field({}, description='数据')

    def json(self):
        """ json """
        return {
            'status': self.status,
            'msg': self.msg,
            'data': self.data
        }

    @property
    def response(self):
        """ response """
        return json.dumps(self.json(), ensure_ascii=False, default=str)
    

if __name__ == '__main__':
    print(StdResponse().response)
    print(StdResponse(status=1, msg="hello", data=["world"]).response)