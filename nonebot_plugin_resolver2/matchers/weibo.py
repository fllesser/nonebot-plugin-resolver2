import os, re, asyncio, json, httpx, math

from nonebot import on_keyword
from nonebot.rule import Rule
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import (
    Message,
    MessageEvent,
    Bot,
    MessageSegment
)

from .filter import is_not_in_disable_group
from .utils import make_node_segment, get_video_seg
from ..constant import COMMON_HEADER
from ..data_source.common import download_img, download_video
from ..config import NICKNAME
# WEIBO_SINGLE_INFO
WEIBO_SINGLE_INFO = "https://m.weibo.cn/statuses/show?id={}"

weibo = on_keyword(
    keywords={"weibo.com", "m.weibo.cn"},
    rule = Rule(is_not_in_disable_group)
)

@weibo.handle()
async def _(bot: Bot, event: MessageEvent):
    message = event.message.extract_plain_text().strip()
    weibo_id = None
    
    # 判断是否包含 "m.weibo.cn"
    # https://m.weibo.cn/detail/4976424138313924
    if match := re.search(r'm\.weibo\.cn(?:/detail|/status)?/([A-Za-z\d]+)', message):
        weibo_id = match.group(1)
    # https://weibo.com/tv/show/1034:5007449447661594?mid=5007452630158934    
    elif match := re.search(r'mid=([A-Za-z\d]+)', message):
        weibo_id = mid2id(match.group(1))
    # 判断是否包含 "weibo.com/show" 且包含 "fid="
    # https://weibo.com/show?fid=1034:5007449447661594
    elif match := re.search(r'(?<=fid=)[\d]+:[\d]+', message):
        logger.info("来个人写写解析fid的（bushi")
        return # 懒得写了
    # 判断是否包含 "weibo.com"
    # https://weibo.com/1707895270/5006106478773472
    elif match := re.search(r'(?<=weibo.com/)[A-Za-z\d]+/[A-Za-z\d]+', message):
        weibo_id = match.group(0)

    # 无法获取到id则返回失败信息
    if not weibo_id:
        await weibo.finish("解析失败：无法获取到微博的 id")
    # 最终获取到的 id
    weibo_id = weibo_id.split("/")[1] if "/" in weibo_id else weibo_id
    # 请求数据
    async with httpx.AsyncClient() as client:
        resp = await client.get(WEIBO_SINGLE_INFO.replace('{}', weibo_id), headers={
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "cookie": "_T_WM=40835919903; WEIBOCN_FROM=1110006030; MLOGIN=0; XSRF-TOKEN=4399c8",
            "Referer": f"https://m.weibo.cn/detail/{weibo_id}",
        } | COMMON_HEADER)
    resp = resp.json()                                                                    
    weibo_data = resp['data']
    # logger.info(weibo_data)
    text, status_title, source, region_name, pics, page_info = (
        weibo_data.get(key) for key in ['text', 'status_title', 'source', 'region_name', 'pics', 'page_info']
    )
    # 发送消息
    await weibo.send(f"{NICKNAME}解析 | 微博 - {re.sub(r'<[^>]+>', '', text)}\n{status_title}\n{source}\t{region_name if region_name else ''}")
    if pics:
        pics = map(lambda x: x['large']['url'], pics)
        download_img_funcs = [asyncio.create_task(
            download_img(url = item, ext_headers={"Referer": "http://blog.sina.com.cn/"})) for item in pics]
        image_paths = await asyncio.gather(*download_img_funcs)
        # 发送图片
        nodes = make_node_segment(bot.self_id, [MessageSegment.image(img_path) for img_path in image_paths])
        # 发送异步后的数据
        await weibo.finish(nodes)

    if page_info:
        video_url = page_info.get('urls', '').get('mp4_720p_mp4', '') or page_info.get('urls', '').get('mp4_hd_mp4', '')
        if video_url:
            video_path = await download_video(video_url, ext_headers={
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "referer": "https://weibo.com/"
            })
            await weibo.finish(await get_video_seg(video_path)) 
            
            
# 定义 base62 编码字符表
ALPHABET = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'


def base62_encode(number):
    """将数字转换为 base62 编码"""
    if number == 0:
        return '0'

    result = ''
    while number > 0:
        result = ALPHABET[number % 62] + result
        number //= 62

    return result


def mid2id(mid):
    mid = str(mid)[::-1]  # 反转输入字符串
    size = math.ceil(len(mid) / 7)  # 计算每个块的大小
    result = []

    for i in range(size):
        # 对每个块进行处理并反转
        s = mid[i * 7:(i + 1) * 7][::-1]
        # 将字符串转为整数后进行 base62 编码
        s = base62_encode(int(s))
        # 如果不是最后一个块并且长度不足4位，进行左侧补零操作
        if i < size - 1 and len(s) < 4:
            s = '0' * (4 - len(s)) + s
        result.append(s)

    result.reverse()  # 反转结果数组
    return ''.join(result)  # 将结果数组连接成字符串
