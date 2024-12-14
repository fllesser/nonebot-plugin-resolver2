import re
import httpx
import aiohttp
import asyncio

from nonebot import on_keyword, logger
from nonebot.rule import Rule
from nonebot.adapters.onebot.v11 import Message, Event, Bot, MessageSegment

from .utils import get_video_seg, make_node_segment
from .filter import is_not_in_disable_group

from ..parser.base import VideoInfo
from ..parser.douyin import DouYin
from ..config import *

douyin = on_keyword(keywords={"douyin.com"}, rule = Rule(is_not_in_disable_group))

douyin_parser = DouYin()

@douyin.handle()
async def _(bot: Bot, event: Event):
    # 消息
    msg: str = event.message.extract_plain_text().strip()
    # 正则匹配
    reg = r"https://(v\.douyin\.com/[a-zA-Z0-9]+|www\.douyin\.com/video/[0-9]+)"
    if match := re.search(reg, msg):
        share_url = match.group(0)
    else:
        logger.info('douyin url is incomplete, ignored')
        return
    try:
        video_info: VideoInfo = await douyin_parser.parse_share_url(share_url)
    except Exception as e:
        await douyin.finish(f"resolve douyin share url err: {e}")
    await douyin.send(f"{NICKNAME}解析 | 抖音 - {video_info.title}")
    if images := video_info.images and len(images) > 0:
        segs = [MessageSegment.image(img_url) for img_url in images]
        await douyin.finish(make_node_segment(bot.self_id, segs))
    if video_url := video_info.video_url:
        await douyin.finish(await get_video_seg(url = video_url))
         