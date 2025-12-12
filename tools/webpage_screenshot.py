"""
网页截图工具
使用 Playwright 捕获网页截图，支持绕过 Cloudflare 验证
"""
import os
from datetime import datetime
from pathlib import Path
from loguru import logger
from config.settings import settings
from langchain_core.tools import tool
from tools.playwright_browser import create_browser


@tool
def capture_webpage_screenshot(
    url: str,
    save_path: str = None,
    full_page: bool = True,
    width: int = 1920,
    height: int = 1080,
    anti_bot: bool = True,
    max_retries: int = 3
) -> str:
    """
    捕获网页截图，支持绕过 Cloudflare 人机验证

    Args:
        url: 要截图的网页URL
        save_path: 截图保存路径，如果为None则自动生成文件名
        full_page: 是否截取整个页面，默认True
        width: 浏览器窗口宽度，默认1920
        height: 浏览器窗口高度，默认1080
        anti_bot: 是否启用反机器人检测（推荐开启以绕过 Cloudflare），默认True
        max_retries: 最大重试次数，默认3次

    Returns:
        截图保存的绝对路径
    """
    browser = None
    try:
        logger.info(f"正在截图网页: {url}")

        # 生成默认保存路径
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            domain = url.split("//")[-1].split("/")[0].replace(".", "_")
            save_path = f"screenshots/screenshot_{domain}_{timestamp}.png"

        # 确保使用绝对路径
        if not os.path.isabs(save_path):
            save_path = os.path.abspath(save_path)

        # 创建浏览器实例
        browser = create_browser(
            headless=settings.headless,
            timeout=settings.timeout
        )

        # 捕获截图
        result_path = browser.capture_screenshot(
            url=url,
            save_path=save_path,
            full_page=full_page,
            width=width,
            height=height,
            anti_bot=anti_bot,
            max_retries=max_retries
        )

        logger.success(f"截图成功保存到: {result_path}")
        return result_path

    except Exception as e:
        error_msg = f"网页截图失败: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

    finally:
        # 确保浏览器被关闭
        if browser:
            try:
                browser.close()
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")

