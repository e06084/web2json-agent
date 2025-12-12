"""
Playwright 浏览器工具
使用 Playwright 获取网页内容，支持绕过 Cloudflare 人机验证
"""
from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PlaywrightTimeout
from loguru import logger
import time
import random
from typing import Optional, Tuple
from pathlib import Path


class PlaywrightBrowser:
    """
    Playwright 浏览器封装类，支持反检测和智能等待
    """

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30000,
        user_agent: Optional[str] = None
    ):
        """
        初始化浏览器

        Args:
            headless: 是否无头模式
            timeout: 默认超时时间（毫秒）
            user_agent: 自定义 User-Agent
        """
        self.headless = headless
        self.timeout = timeout
        self.user_agent = user_agent or self._get_random_user_agent()
        self.playwright = None
        self.browser = None
        self.context = None

    def _get_random_user_agent(self) -> str:
        """获取随机 User-Agent"""
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        ]
        return random.choice(user_agents)

    def start(self):
        """启动浏览器"""
        logger.info("启动 Playwright 浏览器...")
        self.playwright = sync_playwright().start()

        # 启动 Chromium 浏览器
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',  # 禁用自动化控制特征
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )

        # 创建上下文，设置反检测参数
        self.context = self.browser.new_context(
            user_agent=self.user_agent,
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York',
            # 模拟真实浏览器的权限
            permissions=['geolocation', 'notifications'],
        )

        # 注入反检测脚本
        self.context.add_init_script("""
            // 覆盖 navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // 模拟真实的 Chrome
            window.chrome = {
                runtime: {}
            };

            // 覆盖 permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );

            // 覆盖 plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // 覆盖 languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)

        logger.success("浏览器启动成功")

    def close(self):
        """关闭浏览器"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("浏览器已关闭")

    def _wait_for_cloudflare(self, page: Page, max_wait: int = 30) -> bool:
        """
        等待 Cloudflare 验证完成

        Args:
            page: 页面对象
            max_wait: 最大等待时间（秒）

        Returns:
            是否成功通过验证
        """
        logger.info("检测到可能的 Cloudflare 验证，开始智能等待...")

        start_time = time.time()
        last_url = page.url
        check_interval = 0.5  # 每500ms检查一次

        while time.time() - start_time < max_wait:
            try:
                # 检查是否还在验证页面
                current_url = page.url

                # URL 变化可能意味着验证完成
                if current_url != last_url:
                    logger.info(f"检测到 URL 变化: {last_url} -> {current_url}")
                    last_url = current_url
                    time.sleep(2)  # URL变化后再等待2秒确保页面加载

                # 检查页面内容
                try:
                    # 检查是否有 Cloudflare 验证元素
                    has_challenge = page.locator('text=/Checking your browser|Just a moment|Verify you are human/i').count() > 0
                    has_turnstile = page.locator('iframe[src*="challenges.cloudflare.com"]').count() > 0

                    if not has_challenge and not has_turnstile:
                        # 验证已完成，再等待一小段时间确保页面渲染完成
                        logger.success("Cloudflare 验证已完成")
                        time.sleep(2)
                        return True
                    else:
                        logger.debug(f"仍在验证中... (已等待 {int(time.time() - start_time)}秒)")

                except Exception as e:
                    # 如果检查元素时出错，可能是页面已经跳转了
                    logger.debug(f"检查验证状态时出错: {e}")

                time.sleep(check_interval)

            except Exception as e:
                logger.warning(f"等待验证时出错: {e}")
                time.sleep(check_interval)

        logger.warning(f"等待 Cloudflare 验证超时 ({max_wait}秒)")
        return False

    def get_page_content(
        self,
        url: str,
        wait_time: int = 3,
        anti_bot: bool = True,
        max_retries: int = 3
    ) -> Tuple[str, str]:
        """
        获取网页内容

        Args:
            url: 目标 URL
            wait_time: 页面加载后的额外等待时间（秒）
            anti_bot: 是否启用反机器人检测
            max_retries: 最大重试次数

        Returns:
            (html_content, final_url) 元组
        """
        if not self.browser:
            self.start()

        for attempt in range(max_retries):
            try:
                logger.info(f"正在访问网页: {url} (尝试 {attempt + 1}/{max_retries})")

                page = self.context.new_page()
                page.set_default_timeout(self.timeout)

                # 添加随机延迟，模拟人类行为
                if anti_bot and attempt > 0:
                    delay = random.uniform(2, 5)
                    logger.debug(f"随机延迟 {delay:.2f} 秒...")
                    time.sleep(delay)

                # 访问页面
                response = page.goto(url, wait_until='domcontentloaded')

                if response and response.status >= 400:
                    logger.warning(f"HTTP 状态码: {response.status}")

                # 等待网络空闲
                try:
                    page.wait_for_load_state('networkidle', timeout=10000)
                except PlaywrightTimeout:
                    logger.debug("等待网络空闲超时，继续...")

                # 检查是否需要处理 Cloudflare 验证
                if anti_bot:
                    try:
                        # 检查是否有验证挑战
                        has_challenge = page.locator('text=/Checking your browser|Just a moment|Verify you are human/i').count() > 0
                        has_turnstile = page.locator('iframe[src*="challenges.cloudflare.com"]').count() > 0

                        if has_challenge or has_turnstile:
                            success = self._wait_for_cloudflare(page, max_wait=30)
                            if not success:
                                page.close()
                                if attempt < max_retries - 1:
                                    logger.warning(f"验证失败，将进行第 {attempt + 2} 次尝试")
                                    continue
                                else:
                                    raise Exception("无法通过 Cloudflare 验证")
                    except Exception as e:
                        logger.debug(f"检查验证时出错: {e}")

                # 额外等待时间
                if wait_time > 0:
                    logger.debug(f"等待 {wait_time} 秒以确保页面完全加载...")
                    time.sleep(wait_time)

                # 获取最终内容
                html_content = page.content()
                final_url = page.url

                page.close()

                # 验证是否获取到真实内容
                if anti_bot and ('turnstile' in html_content.lower() or 'cf-challenge' in html_content.lower()):
                    logger.warning("检测到页面仍包含验证元素")
                    if attempt < max_retries - 1:
                        logger.info(f"将进行第 {attempt + 2} 次尝试...")
                        continue

                logger.success(f"成功获取网页内容，长度: {len(html_content)} 字符")
                return html_content, final_url

            except Exception as e:
                logger.error(f"获取网页内容失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    wait_seconds = (attempt + 1) * 2
                    logger.info(f"等待 {wait_seconds} 秒后重试...")
                    time.sleep(wait_seconds)
                else:
                    raise Exception(f"获取网页内容失败，已重试 {max_retries} 次: {str(e)}")

    def capture_screenshot(
        self,
        url: str,
        save_path: str,
        full_page: bool = True,
        width: int = 1920,
        height: int = 1080,
        anti_bot: bool = True,
        max_retries: int = 3
    ) -> str:
        """
        捕获网页截图

        Args:
            url: 目标 URL
            save_path: 保存路径
            full_page: 是否截取整个页面
            width: 视口宽度
            height: 视口高度
            anti_bot: 是否启用反机器人检测
            max_retries: 最大重试次数

        Returns:
            保存的文件路径
        """
        if not self.browser:
            self.start()

        for attempt in range(max_retries):
            try:
                logger.info(f"正在截图: {url} (尝试 {attempt + 1}/{max_retries})")

                page = self.context.new_page()
                page.set_viewport_size({"width": width, "height": height})
                page.set_default_timeout(self.timeout)

                # 添加随机延迟
                if anti_bot and attempt > 0:
                    delay = random.uniform(2, 5)
                    time.sleep(delay)

                # 访问页面
                page.goto(url, wait_until='domcontentloaded')

                # 等待网络空闲
                try:
                    page.wait_for_load_state('networkidle', timeout=10000)
                except PlaywrightTimeout:
                    logger.debug("等待网络空闲超时，继续...")

                # 处理验证
                if anti_bot:
                    try:
                        has_challenge = page.locator('text=/Checking your browser|Just a moment|Verify you are human/i').count() > 0
                        has_turnstile = page.locator('iframe[src*="challenges.cloudflare.com"]').count() > 0

                        if has_challenge or has_turnstile:
                            success = self._wait_for_cloudflare(page, max_wait=30)
                            if not success:
                                page.close()
                                if attempt < max_retries - 1:
                                    continue
                                else:
                                    raise Exception("无法通过 Cloudflare 验证")
                    except Exception as e:
                        logger.debug(f"检查验证时出错: {e}")

                # 确保保存目录存在
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)

                # 截图
                page.screenshot(path=save_path, full_page=full_page)

                page.close()

                logger.success(f"截图成功: {save_path}")
                return save_path

            except Exception as e:
                logger.error(f"截图失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    wait_seconds = (attempt + 1) * 2
                    time.sleep(wait_seconds)
                else:
                    raise Exception(f"截图失败，已重试 {max_retries} 次: {str(e)}")


def create_browser(headless: bool = True, timeout: int = 30000) -> PlaywrightBrowser:
    """
    创建浏览器实例的便捷函数

    Args:
        headless: 是否无头模式
        timeout: 超时时间（毫秒）

    Returns:
        PlaywrightBrowser 实例
    """
    return PlaywrightBrowser(headless=headless, timeout=timeout)
