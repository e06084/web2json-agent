"""
XPath生成 API

简化版：只有一个核心endpoint
"""
from fastapi import APIRouter, HTTPException
from loguru import logger

from web2json_api.models.xpath import XPathGenerateRequest, XPathGenerateResponse
from web2json_api.services.xpath_service import xpath_service

router = APIRouter()


@router.post("/generate", response_model=XPathGenerateResponse)
async def generate_xpaths(request: XPathGenerateRequest):
    """
    生成XPath表达式

    **核心功能：**
    1. 接收HTML内容或URL
    2. 接收字段定义
    3. 调用agent生成XPath
    4. 返回包含XPath的字段列表

    **请求示例1（HTML内容）：**
    ```json
    {
      "html_content": "<html><body><h1>Title</h1><span class='price'>$99.99</span></body></html>",
      "url": null,
      "fields": [
        {"name": "title", "description": "Page title", "field_type": "string"},
        {"name": "price", "description": "Product price", "field_type": "string"}
      ]
    }
    ```

    **请求示例2（URL）：**
    ```json
    {
      "html_content": null,
      "url": "https://example.com/product/123",
      "fields": [
        {"name": "title", "description": "Page title", "field_type": "string"},
        {"name": "price", "description": "Product price", "field_type": "string"}
      ]
    }
    ```

    **响应示例：**
    ```json
    {
      "success": true,
      "fields": [
        {
          "name": "title",
          "xpath": "//h1/text()",
          "value_sample": ["Title"]
        },
        {
          "name": "price",
          "xpath": "//span[@class='price']/text()",
          "value_sample": ["$99.99"]
        }
      ]
    }
    ```
    """
    try:
        # 验证输入
        if not request.html_content and not request.url:
            raise HTTPException(
                status_code=400,
                detail="Must provide either html_content or url"
            )

        if request.html_content and request.url:
            raise HTTPException(
                status_code=400,
                detail="Cannot provide both html_content and url, choose one"
            )

        if not request.fields or len(request.fields) == 0:
            raise HTTPException(status_code=400, detail="At least one field is required")

        logger.info(f"收到XPath生成请求: {len(request.fields)} 个字段")
        if request.url:
            logger.info(f"输入方式: URL - {request.url}")
        else:
            logger.info(f"输入方式: HTML内容 ({len(request.html_content)} 字符)")

        # 调用服务生成XPath
        output_fields = xpath_service.generate_xpaths(
            html_content=request.html_content,
            url=request.url,
            fields=request.fields
        )

        return XPathGenerateResponse(
            success=True,
            fields=output_fields,
            message=f"Successfully generated XPath for {len(output_fields)} field(s)"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"XPath生成失败: {str(e)}")
        return XPathGenerateResponse(
            success=False,
            fields=[],
            error=str(e),
            message="Failed to generate XPath"
        )
