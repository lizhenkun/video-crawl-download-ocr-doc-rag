#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field
from app.agents.base_knowleage_agent import BaseKnowleageAgent


class YouHeGaoJianAgent(BaseKnowleageAgent):
    """
    基础知识博主Agent
    """
    name: str = Field("有何高见", description="博主名，也是 agent 的名字")
    