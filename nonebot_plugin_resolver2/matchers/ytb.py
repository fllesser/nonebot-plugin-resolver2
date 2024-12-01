import re

from nonebot import on_regex
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment
from nonebot.typing import T_State
from nonebot.params import Arg
from .filter import resolve_filter
from .utils import get_video_seg, get_file_seg
from ..core.ytdlp import *
from ..config import *

ytb = on_regex(
    r"(youtube.com|youtu.be)", priority=1
)

@ytb.handle()
@resolve_filter
async def _(event: MessageEvent, state: T_State):
    url = re.search(
        r"(?:https?:\/\/)?(www\.)?youtube\.com\/[A-Za-z\d._?%&+\-=\/#]*|(?:https?:\/\/)?youtu\.be\/[A-Za-z\d._?%&+\-=\/#]*",
        str(event.message).strip())[0]
    try:
        title = await get_video_title(url, YTB_COOKIES_FILE, PROXY)
        await ytb.send(f"{NICKNAME}解析 | 油管 - {title}")
    except Exception as e:
        await ytb.send(f"{NICKNAME}解析 | 油管 - 标题获取出错: {e}")
    state["url"] = url

@ytb.got("type", prompt="您需要下载音频(0)，还是视频(1)")
async def _(state: T_State, type: Message = Arg()):
    url: str = state["url"]
    seg: MessageSegment = MessageSegment.text("下载失败")
    try:
        if int(type.extract_plain_text()) == 1:
            video_path = await ytdlp_download_video(
                url = url, type="ytb", cookiefile = YTB_COOKIES_FILE, proxy = PROXY)
            seg = await get_video_seg(video_path)
        else: 
            audio_path = await ytdlp_download_audio(
                url = url, type="ytb", cookiefile = YTB_COOKIES_FILE, proxy = PROXY)
            seg = await get_file_seg(audio_path)
        await ytb.send(seg)
    except Exception as e:
        await ytb.send(f"下载失败 | {e}")
    