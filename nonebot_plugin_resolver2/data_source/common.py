import os
import re
import json
import time
import httpx
import asyncio
import aiofiles
import subprocess

from pathlib import Path
from nonebot.log import logger
from tqdm.asyncio import tqdm
from urllib.parse import urlparse

from ..constant import COMMON_HEADER
from ..config import plugin_cache_dir


class Downloader:
    
    def __init__(
        self,
        url: str,
        file_name: str = "",
        proxy: str = "",
        ext_headers: dict[str, str] = {}
    ):
        if not url:
            raise EmptyURLError("url cannot be empty")
        self.url = url
        self.file_name = file_name
        self.client_config = self.get_client_base_config()
        self.client_config['headers'] = COMMON_HEADER | ext_headers
        if proxy:
            self.client_config['proxies'] = { 
                'http://': proxy,
                'https://': proxy 
            }
    
    def get_client_base_config(self) -> dict[str, str]:
        return {
            'timeout': httpx.Timeout(60, connect=5.0),
            'follow_redirects': True
        }
    
    async def download_file_by_stream(self) -> Path:
        file_path = plugin_cache_dir / self.file_name
        if file_path.exists():
            return file_path
        async with httpx.AsyncClient(**self.client_config) as client:
            async with client.stream("GET", self.url) as resp:
                if resp.status_code >= 400:
                    resp.raise_for_status()
                with tqdm(
                    total=int(resp.headers.get('content-length', 0)),
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    dynamic_ncols=True,
                    colour='green'
                ) as bar:
                    # 设置前缀信息
                    bar.set_description(self.file_name)
                    async with aiofiles.open(file_path, "wb") as f:
                        async for chunk in resp.aiter_bytes():
                            await f.write(chunk)
                            bar.update(len(chunk))
        return file_path
    
    
def parse_url_resource_name(url: str) -> str:
    url_paths = urlparse(url).path.split('/')
    # 过滤掉空字符串并去除两端空白
    filtered_paths = [segment.strip() for segment in url_paths if segment.strip()]
    # 获取最后一个非空路径段
    return filtered_paths[-1] if filtered_paths else str(time.time())

async def download_video(
    url: str,
    video_name: str = "",
    proxy: str = "",
    ext_headers: dict[str, str] = {}
) -> Path:
    if not video_name:
        video_name = parse_url_resource_name(url).split(".")[0] + ".mp4"
    downer = Downloader(url, video_name, proxy, ext_headers)
    return await downer.download_file_by_stream()

async def download_audio(
    url: str,
    audio_name: str = "",
    proxy: str = "",
    ext_headers: dict[str, str] = {}
) -> Path:
    if not audio_name:
        audio_name = parse_url_resource_name(url)
    downer = Downloader(url, audio_name, proxy, ext_headers)
    return await self.download_file_by_stream()

async def download_img(
    url: str,
    img_name: str = "",
    proxy: str = "",
    ext_headers: dict[str, str] = {}
) -> Path:
    if not img_name:
        img_name = parse_url_resource_name(url)
    downer = Downloader(url, img_name, proxy, ext_headers)
    return await self.download_file_by_stream()
    
async def merge_av(
    v_path: Path,
    a_path: Path,
    output_path: Path,
    log_output: bool = False
):
    """
    合并视频文件和音频文件
    """
    logger.info(f'正在合并: {output_path.name}')
    # 构建 ffmpeg 命令, localstore already path.resolve()
    command = f'ffmpeg -y -i {v_path} -i "{a_path}" -c copy "{output_path}"'
    stdout = None if log_output else subprocess.DEVNULL
    stderr = None if log_output else subprocess.DEVNULL
    await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: subprocess.call(command, shell=True, stdout=stdout, stderr=stderr)
    )

def delete_boring_characters(sentence: str) -> str:
    """
        去除标题的特殊字符
    :param sentence:
    :return:
    """
    return re.sub(r'[’!"∀〃\$%&\'\(\)\*\+,\./:;<=>\?@，。?★、…【】《》？“”‘’！\[\\\]\^_`\{\|\}~～]+', "", sentence)

class EmptyURLError(Exception):
    pass