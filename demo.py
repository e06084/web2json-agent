#!/usr/bin/env python3
"""
Web2JSON 解析器通用 Demo 脚本
支持使用生成的任何解析器进行单文件、URL或批量解析

用法:
    # 使用指定的解析器
    python demo.py -p output/blog/final_parser.py <html_file>
    python demo.py -p output/blog/final_parser.py <url>
    python demo.py -p output/blog/final_parser.py -d <html_directory>

    # 自动使用最新的解析器
    python demo.py <html_file>
    python demo.py -d <html_directory>
    python demo.py -d <html_directory> -o results.json
"""

import sys
import json
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Optional


def find_latest_parser() -> Optional[Path]:
    """
    自动查找output目录下最新的解析器

    Returns:
        最新解析器的路径，如果未找到则返回None
    """
    output_dir = Path(__file__).parent / "output"
    if not output_dir.exists():
        return None

    # 查找所有final_parser.py文件
    parsers = []
    for subdir in output_dir.iterdir():
        if subdir.is_dir():
            # 首先尝试在 parsers 子目录下查找
            parser_file = subdir / "parsers" / "final_parser.py"
            if parser_file.exists():
                parsers.append(parser_file)
            else:
                # 兼容旧版本，也在子目录直接查找
                parser_file = subdir / "final_parser.py"
                if parser_file.exists():
                    parsers.append(parser_file)

    if not parsers:
        return None

    # 返回最新的（按修改时间）
    return max(parsers, key=lambda p: p.stat().st_mtime)


def load_parser(parser_path: Path):
    """
    动态加载解析器类

    Args:
        parser_path: 解析器文件路径

    Returns:
        WebPageParser实例
    """
    spec = importlib.util.spec_from_file_location("parser_module", parser_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["parser_module"] = module
    spec.loader.exec_module(module)

    if hasattr(module, 'WebPageParser'):
        return module.WebPageParser()
    else:
        raise AttributeError(f"解析器文件中未找到 WebPageParser 类: {parser_path}")


def parse_single(parser, input_source: str) -> Dict[str, Any]:
    """
    解析单个HTML文件或URL

    Args:
        parser: WebPageParser实例
        input_source: HTML文件路径或URL

    Returns:
        解析结果字典
    """
    # 判断是URL还是文件
    if input_source.startswith('http://') or input_source.startswith('https://'):
        try:
            from DrissionPage import ChromiumPage
        except ImportError:
            return {'error': 'DrissionPage未安装。请运行: pip install DrissionPage'}

        print(f"正在抓取URL: {input_source}")
        page = ChromiumPage()
        page.get(input_source)
        html_content = page.html
        page.quit()
    else:
        html_file = Path(input_source)
        if not html_file.exists():
            return {'error': f'文件不存在: {html_file}'}

        print(f"正在解析文件: {html_file}")
        html_content = html_file.read_text(encoding='utf-8')

    return parser.parse(html_content)


def parse_batch(parser, html_dir: str, output_file: str = None) -> List[Dict[str, Any]]:
    """
    批量解析目录下的所有HTML文件

    Args:
        parser: WebPageParser实例
        html_dir: HTML文件所在目录
        output_file: 可选，保存结果的文件路径

    Returns:
        解析结果列表
    """
    html_path = Path(html_dir)
    if not html_path.exists() or not html_path.is_dir():
        print(f"错误: 目录不存在 - {html_dir}")
        return []

    html_files = list(html_path.glob("*.html"))
    if not html_files:
        print(f"警告: 目录中没有HTML文件 - {html_dir}")
        return []

    print(f"\n找到 {len(html_files)} 个HTML文件")
    results = []

    for idx, html_file in enumerate(html_files, 1):
        print(f"\n[{idx}/{len(html_files)}] 正在解析: {html_file.name}")

        try:
            html_content = html_file.read_text(encoding='utf-8')
            result = parser.parse(html_content)
            result['_source_file'] = html_file.name
            results.append(result)
            print(f"  ✓ 解析成功")
        except Exception as e:
            print(f"  ✗ 解析失败: {str(e)}")
            results.append({
                '_source_file': html_file.name,
                'error': str(e)
            })

    # 保存结果
    if output_file:
        output_path = Path(output_file)
        output_path.write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        print(f"\n✓ 结果已保存到: {output_file}")

    return results


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    # 解析命令行参数
    args = sys.argv[1:]
    parser_path = None

    # 检查是否指定了解析器路径
    if '-p' in args:
        parser_idx = args.index('-p')
        if parser_idx + 1 >= len(args):
            print("错误: -p 参数需要指定解析器路径")
            sys.exit(1)
        parser_path = Path(args[parser_idx + 1])
        # 移除 -p 和路径参数
        args = args[:parser_idx] + args[parser_idx + 2:]
    else:
        # 自动查找最新的解析器
        parser_path = find_latest_parser()
        if not parser_path:
            print("错误: 未找到解析器文件")
            print("请使用 -p 参数指定解析器路径，或先运行 web2json 生成解析器")
            sys.exit(1)
        print(f"使用解析器: {parser_path}")

    if not parser_path.exists():
        print(f"错误: 解析器文件不存在 - {parser_path}")
        sys.exit(1)

    # 加载解析器
    try:
        parser = load_parser(parser_path)
    except Exception as e:
        print(f"错误: 加载解析器失败 - {str(e)}")
        sys.exit(1)

    # 批量处理模式
    if '-d' in args:
        dir_idx = args.index('-d')
        if dir_idx + 1 >= len(args):
            print("错误: -d 参数需要指定目录路径")
            sys.exit(1)

        html_dir = args[dir_idx + 1]

        # 检查是否指定输出文件
        output_file = None
        if '-o' in args:
            out_idx = args.index('-o')
            if out_idx + 1 < len(args):
                output_file = args[out_idx + 1]

        results = parse_batch(parser, html_dir, output_file)

        # 如果没有指定输出文件，打印到控制台
        if not output_file and results:
            print("\n" + "="*50)
            print("解析结果:")
            print("="*50)
            print(json.dumps(results, ensure_ascii=False, indent=2))

    # 单文件处理模式
    else:
        if not args:
            print("错误: 请指定HTML文件路径或URL")
            sys.exit(1)

        input_source = args[0]
        result = parse_single(parser, input_source)

        print("\n" + "="*50)
        print("解析结果:")
        print("="*50)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
