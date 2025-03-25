from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment
from nonebot.plugin.on import on_keyword
from nonebot.rule import Rule

from nonebot_plugin_resolver2.config import NICKNAME
from nonebot_plugin_resolver2.download import download_imgs_without_raise, download_video
from nonebot_plugin_resolver2.parsers.weibo import ParseException, WeiBo

from .filter import is_not_in_disabled_groups
from .utils import get_video_seg, send_segments

weibo_parser = WeiBo()

weibo = on_keyword(keywords={"weibo.com", "m.weibo.cn"}, rule=Rule(is_not_in_disabled_groups))


@weibo.handle()
async def _(event: MessageEvent):
    message = event.message.extract_plain_text().strip()
    pub_prefix = f"{NICKNAME}解析 | 微博 - "
    try:
        video_info = await weibo_parser.parse_share_url(message)
    except ParseException as e:
        await weibo.finish(f"{pub_prefix}解析失败: {e}")

    ext_headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",  # noqa: E501
        "referer": "https://weibo.com/",
    }
    await weibo.send(f"{pub_prefix}{video_info.title} - {video_info.author.name}")
    if video_info.video_url:
        video_path = await download_video(video_info.video_url, ext_headers=ext_headers)
        await weibo.finish(await get_video_seg(video_path))
    if video_info.images:
        image_paths = await download_imgs_without_raise(video_info.images, ext_headers=ext_headers)
        await send_segments(weibo, [MessageSegment.image(f) for f in image_paths])
