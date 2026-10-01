#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field


class BaseKnowleageAgent(BaseModel):
    """
    基础知识博主Agent
    """
    name: str = Field(..., description="博主名，也是 agent 的名字")
    