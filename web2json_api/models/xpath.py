"""
XPath生成相关模型
"""
from typing import List, Optional
from pydantic import BaseModel, Field

from .field import FieldInput, FieldOutput


class XPathGenerateRequest(BaseModel):
    """
    XPath生成请求

    用户提供两种方式之一：
    1. 直接提供HTML内容 (html_content)
    2. 提供URL (url)

    以及需要抽取的字段列表
    """
    html_content: Optional[str] = Field(None, description="HTML内容（与url二选一）")
    url: Optional[str] = Field(None, description="网页URL（与html_content二选一）")
    fields: List[FieldInput] = Field(..., description="需要抽取的字段列表")

    class Config:
        json_schema_extra = {
            "example": {
                "html_content": "<html><body><h1>Title</h1><span class='price'>$99.99</span></body></html>",
                "url": None,
                "fields": [
                    {"name": "title", "description": "Page title", "field_type": "string"},
                    {"name": "price", "description": "Product price", "field_type": "string"}
                ]
            }
        }


class XPathGenerateResponse(BaseModel):
    """
    XPath生成响应

    返回每个字段对应的XPath表达式
    """
    success: bool = Field(..., description="是否成功")
    fields: List[FieldOutput] = Field(..., description="包含生成XPath的字段列表")
    error: Optional[str] = Field(None, description="错误信息")
    message: Optional[str] = Field(None, description="提示信息")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "fields": [
                    {
                        "name": "title",
                        "description": "Page title",
                        "field_type": "string",
                        "xpath": "//h1/text()",
                        "value_sample": ["Title"]
                    },
                    {
                        "name": "price",
                        "description": "Product price",
                        "field_type": "string",
                        "xpath": "//span[@class='price']/text()",
                        "value_sample": ["$99.99"]
                    }
                ],
                "error": None,
                "message": "Successfully generated XPath for 2 fields"
            }
        }
