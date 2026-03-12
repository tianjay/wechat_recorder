import json
from pathlib import Path
from loguru import logger
from typing import List, Dict, Optional

class MessageStitcher:
    """
    负责将新扫描到的页面消息与历史消息进行拼接去重。
    策略：
    1. 维护上一页的消息列表 (last_page_messages)
    2. 获取当前页的消息列表 (current_page_messages)
    3. 寻找 current_page_messages 的顶部与 last_page_messages 的底部的重叠部分
    4. 返回新增的消息部分
    """
    def __init__(self):
        self.last_page_messages: List[Dict] = []
        self.seen_hashes = set() # 全局去重，防止循环滚动导致的重复
        
    def stitch(self, current_page_messages: List[Dict]) -> List[Dict]:
        """
        输入当前页抓取到的所有消息（按屏幕从上到下排序），
        返回去重后的新增消息列表。
        """
        if not current_page_messages:
            return []
            
        # 1. 简单去重：过滤掉全局已见过的 hash
        # 注意：对于完全相同的文本（"收到"），这种去重可能会误杀
        # 但结合滚动逻辑，我们假设短时间内不会出现大量重复文本且无法区分
        # 如果需要更精确，应该结合位置或上下文
        
        # 改进策略：寻找重叠区域
        # 假设重叠至少有 1 条消息（如果不重叠，说明滚过头了，会有数据丢失风险）
        # 我们尝试匹配 current_page 的前 N 条 与 last_page 的后 N 条
        
        if not self.last_page_messages:
            self.last_page_messages = current_page_messages
            # 首次，全部返回
            return current_page_messages
            
        # 寻找切割点
        # 倒序遍历 last_page，尝试在 current_page 中找到匹配点
        # last_page: [A, B, C, D, E]
        # current:      [C, D, E, F, G]
        # overlap: C, D, E
        # new: F, G
        
        overlap_size = 0
        max_overlap_check = min(len(self.last_page_messages), len(current_page_messages))
        
        # 增强匹配策略：允许部分匹配失败（针对 COPY_FAILED 的情况）
        for size in range(max_overlap_check, 0, -1):
            # 取 last_page 的最后 size 个
            suffix = self.last_page_messages[-size:]
            # 取 current_page 的前 size 个
            prefix = current_page_messages[:size]
            
            # 比较 hash 序列
            # 如果是 COPY_FAILED，则视为通配符，可以匹配任何内容
            match_count = 0
            for a, b in zip(suffix, prefix):
                if a['content'] == "<COPY_FAILED>" or b['content'] == "<COPY_FAILED>":
                    # 占位符视为匹配
                    match_count += 1
                elif a['hash'] == b['hash']:
                    match_count += 1
            
            # 如果匹配率超过 80%，则认为找到了重叠区域
            # 对于小样本 (size < 3)，要求 100% 匹配
            threshold = 1.0 if size < 3 else 0.8
            
            if match_count / size >= threshold:
                overlap_size = size
                break
                
        # 新消息是 current_page 中去除重叠部分后的内容
        new_messages = current_page_messages[overlap_size:]
        
        if overlap_size > 0:
            logger.debug(f"找到重叠区域 {overlap_size} 条，新增 {len(new_messages)} 条")
        else:
            # 即使没有找到连续的重叠区域，也尝试进行逐条去重（针对滚坏了或者无重叠的情况）
            # 这是一种兜底策略，防止全部重复
            # 检查 current_page 的第一条是否在 last_page 中出现过
            if current_page_messages and self.last_page_messages:
                first_new = current_page_messages[0]
                # 在 last_page 中查找 first_new
                # 仅查找 last_page 的后半部分，避免很久以前的重复消息干扰
                search_scope = self.last_page_messages[len(self.last_page_messages)//2:]
                for i, msg in enumerate(search_scope):
                    if msg['hash'] == first_new['hash'] and msg['content'] != "<COPY_FAILED>":
                        # 找到了第一条消息在上一页的位置
                        # 假设这是一个断裂的重叠，虽然序列不匹配，但我们可以认为 first_new 是旧的
                        logger.warning(f"序列匹配失败，但在上一页找到了首条消息 {first_new['content'][:10]}，尝试丢弃...")
                        # 这是一个非常激进的假设：如果第一条是旧的，那么它之前的所有（这里没有之前）和它自己都是旧的
                        # 我们不仅要丢弃这一条，还要看看后续的是否也能匹配上
                        # 简单起见，如果第一条重复，我们就假设它是重叠的开始（虽然 overlap_size=0 计算失败了）
                        # 这可能还是不够安全。
                        # 安全的做法：只打印警告。
                        pass

            logger.warning("未找到重叠区域！可能滚动过快导致漏消息，或者恰好无重叠。")
            
        # 更新 last_page
        self.last_page_messages = current_page_messages
        
        return new_messages
