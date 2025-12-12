#!/bin/bash

echo "======================================"
echo "Playwright Cloudflare 绕过方案 - 安装"
echo "======================================"
echo ""

# 检查 Python 版本
echo "[1/4] 检查 Python 环境..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 版本: $python_version"
echo ""

# 安装 Python 依赖
echo "[2/4] 安装 Python 依赖..."
pip install playwright==1.48.0
if [ $? -eq 0 ]; then
    echo "✅ Playwright 安装成功"
else
    echo "❌ Playwright 安装失败"
    exit 1
fi
echo ""

# 安装 Playwright 浏览器
echo "[3/4] 安装 Playwright Chromium 浏览器..."
python3 -m playwright install chromium
if [ $? -eq 0 ]; then
    echo "✅ Chromium 安装成功"
else
    echo "❌ Chromium 安装失败"
    exit 1
fi
echo ""

# 安装其他依赖
echo "[4/4] 安装其他项目依赖..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✅ 项目依赖安装成功"
else
    echo "⚠️ 部分依赖安装失败，请检查"
fi
echo ""

echo "======================================"
echo "✅ 安装完成！"
echo "======================================"
echo ""
echo "下一步："
echo "1. 运行测试: python test_captcha_handling.py"
echo "2. 查看文档: doc/playwright_cloudflare_bypass.md"
echo ""
