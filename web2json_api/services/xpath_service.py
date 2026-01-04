"""
XPath生成服务

对接 web2json agent 的 enrich_schema_with_xpath() 函数
"""
from typing import List, Dict, Optional
from loguru import logger
import requests

from web2json.tools.schema_extraction import enrich_schema_with_xpath
from web2json_api.models.field import FieldInput, FieldOutput


class XPathService:
    """
    XPath生成服务

    核心功能：将用户定义的字段转换为schema模板，
    调用agent生成XPath，然后转换回字段格式返回前端
    """

    @staticmethod
    def fetch_html_from_url(url: str) -> str:
        """
        从URL获取HTML内容

        Args:
            url: 网页URL

        Returns:
            HTML内容

        Raises:
            Exception: 获取失败时抛出异常
        """
        try:
            logger.info(f"正在从URL获取HTML: {url}")

            # 设置请求头，模拟浏览器
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # 尝试使用正确的编码
            response.encoding = response.apparent_encoding
            html_content = response.text

            logger.success(f"成功获取HTML，长度: {len(html_content)} 字符")
            return html_content

        except Exception as e:
            logger.error(f"从URL获取HTML失败: {str(e)}")
            raise Exception(f"无法访问URL: {str(e)}")

    @staticmethod
    def generate_xpaths(
        html_content: Optional[str],
        url: Optional[str],
        fields: List[FieldInput]
    ) -> List[FieldOutput]:
        """
        为所有字段生成XPath

        Args:
            html_content: HTML内容（可选）
            url: 网页URL（可选）
            fields: 用户定义的字段列表

        Returns:
            包含XPath的字段列表

        Raises:
            Exception: 生成失败时抛出异常
        """
        try:
            # 1. 验证输入：必须提供html_content或url之一
            if not html_content and not url:
                raise ValueError("必须提供html_content或url之一")

            if html_content and url:
                raise ValueError("html_content和url只能提供其中之一")

            # 2. 如果提供的是URL，先获取HTML
            if url:
                html_content = XPathService.fetch_html_from_url(url)

            logger.info(f"开始为 {len(fields)} 个字段生成XPath...")
            logger.info(f"HTML长度: {len(html_content)} 字符")

            # 3. 转换为agent需要的schema_template格式
            schema_template = {}
            for field in fields:
                schema_template[field.name] = {
                    "type": field.field_type,
                    "description": field.description or "",
                    "value_sample": [],
                    "xpaths": [""]  # 空的，等待agent生成
                }

            logger.info(f"Schema模板: {list(schema_template.keys())}")

            # 2. 调用agent的enrich_schema_with_xpath函数
            # 这是核心：复用现有agent逻辑
            # 注意：enrich_schema_with_xpath被@tool装饰器包装，需要使用.invoke()
            enriched_schema = enrich_schema_with_xpath.invoke({
                "schema_template": schema_template,
                "html_content": html_content
            })

            logger.info("Agent成功生成XPath")

            # 3. 转换回前端需要的格式
            output_fields = []
            for field in fields:
                field_name = field.name
                if field_name in enriched_schema:
                    enriched_data = enriched_schema[field_name]

                    # 提取XPath（可能是列表，取第一个）
                    xpaths = enriched_data.get("xpaths", [""])
                    xpath = xpaths[0] if isinstance(xpaths, list) and xpaths else str(xpaths or "")

                    # 提取value_sample（可能是列表或字符串）
                    value_sample_raw = enriched_data.get("value_sample", [])
                    if isinstance(value_sample_raw, list):
                        value_sample = value_sample_raw
                    elif value_sample_raw:
                        value_sample = [str(value_sample_raw)]
                    else:
                        value_sample = []

                    output_fields.append(FieldOutput(
                        name=field_name,
                        description=field.description,
                        field_type=field.field_type,
                        xpath=xpath,
                        value_sample=value_sample
                    ))
                else:
                    # 如果agent没有返回该字段，使用空XPath
                    logger.warning(f"字段 {field_name} 未在返回结果中找到")
                    output_fields.append(FieldOutput(
                        name=field_name,
                        description=field.description,
                        field_type=field.field_type,
                        xpath="",
                        value_sample=[]
                    ))

            logger.success(f"成功为 {len(output_fields)} 个字段生成XPath")
            return output_fields

        except Exception as e:
            logger.error(f"生成XPath失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise Exception(f"XPath生成失败: {str(e)}")


# 全局实例
xpath_service = XPathService()
