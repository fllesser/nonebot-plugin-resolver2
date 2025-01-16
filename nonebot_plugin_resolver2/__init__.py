from nonebot import get_driver, logger

from nonebot.plugin import PluginMetadata
from .matchers import resolvers
from .config import (
    Config,
    rconfig,
    scheduler,
    plugin_cache_dir,
    ytb_cookies_file,
)
from .cookie import save_cookies_to_netscape


__plugin_meta__ = PluginMetadata(
    name="链接分享解析器重制版",
    description="NoneBot2 链接分享解析器插件, 支持的解析，BV号/链接/小程序/卡片，支持平台：b站，抖音，网易云，微博，小红书，youtube，tiktok，twitter等",
    usage="发送支持平台的(BV号/链接/小程序/卡片)即可",
    type="application",
    homepage="https://github.com/fllesser/nonebot-plugin-resolver2",
    config=Config,
    supported_adapters={ "~onebot.v11" }
)

@get_driver().on_startup
async def _():
    if not rconfig.r_bili_ck:
        logger.warning('未配置哔哩哔哩 cookie，无法使用哔哩哔哩AI总结，可能无法解析 720p 以上画质视频')
    if rconfig.r_ytb_ck:
        save_cookies_to_netscape(rconfig.r_ytb_ck, ytb_cookies_file, 'youtube.com')
    if not rconfig.r_xhs_ck:
        if xiaohongshu := resolvers.pop("xiaohongshu", None):
            xiaohongshu.destroy()
            logger.warning("未配置小红书 cookie, 小红书解析器已销毁")
    # 处理黑名单 resovler
    for resolver in rconfig.r_disable_resolvers:
        if matcher := resolvers.get(resolver, None):
            matcher.destroy()
            logger.warning(f"解析器 {resolver} 已销毁")

@scheduler.scheduled_job(
    "cron",
    hour=1,
    minute=0,
    id = "resolver2-clean-local-cache"
)
async def _():
    for file in plugin_cache_dir.iterdir():
        if file.is_file():
            file.unlink()