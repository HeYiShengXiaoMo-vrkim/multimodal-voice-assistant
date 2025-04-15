"""
使用 DuckDuckGo 进行网页搜索并处理结果。
"""
import re
from duckduckgo_search import DDGS
from logger import log

def duckduckgo_search(query, max_results=3):
    """使用 DuckDuckGo 进行网页搜索"""
    log(f"正在搜索: {query}", title="SEARCH", style="blue")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        log(f"找到 {len(results)} 条搜索结果", title="SEARCH", style="blue")
        return results
    except Exception as e:
        log(f"DuckDuckGo 搜索出错: {str(e)}", title="ERROR", style="bold red")
        return []

def process_search_results(results):
    """格式化搜索结果以便 LLM 理解"""
    if not results:
        return "没有找到相关信息。"
    processed = "以下是相关的网页搜索结果摘要:\n\n"
    for i, result in enumerate(results, 1):
        title = result.get('title', '无标题')
        body = result.get('body', '无内容').strip()
        href = result.get('href', '无链接')
        body_summary = re.sub(r'\s+', ' ', body)[:250] # 清理并截断
        processed += f"{i}. **{title}**\n   *摘要*: {body_summary}...\n   *链接*: {href}\n\n"
    return processed