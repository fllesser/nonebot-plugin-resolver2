import re

from nonebot.log import logger
from nonebot.typing import T_State
from nonebot.plugin.on import on_message
from nonebot.adapters.onebot.v11 import MessageSegment
from .utils import get_file_seg
from .filter import is_not_in_disabled_groups
from .preprocess import r_keywords, R_EXTRACT_KEY
from ..parsers.kugou import KuGou
from ..download.common import download_audio
from ..config import NICKNAME


kugou = on_message(rule=is_not_in_disabled_groups & r_keywords("kugou.com"))
kugou_parser = KuGou()


@kugou.handle()
async def _(state: T_State):
    text = state.get(R_EXTRACT_KEY, "")
    # https://t1.kugou.com/song.html?id=1hfw6baEmV3
    pattern = r"https?://.*kugou\.com.*id=[a-zA-Z0-9]+"
    # pattern = r"https?://.*?kugou\.com.*?(?=\s|$|\n)"
    if match := re.search(pattern, text):
        url = match.group(0)
    else:
        logger.info(f"无效链接，忽略 - {text}")
        return
    try:
        video_info = await kugou_parser.parse_share_url(url)
    except Exception as e:
        await kugou.finish(f"{NICKNAME}解析 | 解析失败: {e}")

    title_author_name = f"{video_info.title} - {video_info.author.name}"

    await kugou.send(
        f"{NICKNAME}解析 | {title_author_name}"
        + MessageSegment.image(video_info.cover_url)
    )
    filename = f"{title_author_name}.mp3"
    audio_path = await download_audio(url=video_info.music_url, audio_name=filename)
    # 发送语音
    await kugou.send(MessageSegment.record(audio_path))
    # 发送群文件
    await kugou.finish(get_file_seg(audio_path, filename))
