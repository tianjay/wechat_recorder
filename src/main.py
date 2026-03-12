import sys
import time
import random
import json
import hashlib
from pathlib import Path
from loguru import logger
from src.core.automation import WeChatAutomation
from src.utils.stitcher import MessageStitcher

def compute_hash(content: str, sender: str) -> str:
    raw = f"{sender}:{content}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()

def parse_clipboard_content(text: str, msg_type: str) -> dict:
    if msg_type == 'Time':
        sender = 'System'
    else:
        sender = "Friend" if msg_type == 'Left' else "Self"
        
    return {
        "sender_type": sender,
        "content": text,
        "timestamp": int(time.time())
    }

def save_message_to_jsonl(file_path: Path, message: dict):
    """追加写入 JSONL 文件"""
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(message, ensure_ascii=False) + "\n")

def main():
    logger.add("wechat_recorder.log")
    automation = WeChatAutomation()
    stitcher = MessageStitcher()
    
    if not automation.connect():
        return
        
    output_file = Path("data/chat_history_live.jsonl")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("已连接微信窗口，开始初始化布局分析...")
    
    # 1. 滚动到顶部 (智能检测)
    # 用户要求："首先,无限制速度的尽量快的滑动到消息框的最顶端,从第一条开始"
    automation.scroll_to_top()
        
    all_messages = []
        
    no_new_data_count = 0
    max_no_new_limit = 5 # 增加容错，因为小步滚动可能需要更多次确认
    
    logger.info("开始抓取流程 (JSONL 实时保存模式)...")
    
    while True:
        # 1. 扫描当前屏幕所有元素
        logger.info("扫描屏幕布局...")
        regions = automation.scan_messages()
        total_regions = len(regions)
        logger.info(f"发现 {total_regions} 个元素")
        
        current_page_data = []
        
        # 2. 依次抓取内容
        for idx, region in enumerate(regions):
            logger.info(f"正在抓取第 {idx+1}/{total_regions} 条消息...")
            content = automation.click_and_copy(region.center_x, region.center_y)
            
            if content:
                parsed = parse_clipboard_content(content, region.type)
                parsed['hash'] = compute_hash(content, region.type)
                
                if region.type == 'Time' and len(content) > 100:
                     parsed['sender_type'] = 'System_Likely_Text'

                current_page_data.append(parsed)
            else:
                # 即使复制失败，也保留占位符，以保持序列结构完整，利于去重
                if region.type != 'Time':
                    logger.warning(f"无法复制内容: ({region.center_x}, {region.center_y})")
                    # 创建占位消息
                    placeholder = {
                        "sender_type": "Unknown",
                        "content": "<COPY_FAILED>",
                        "timestamp": int(time.time()),
                        "hash": f"COPY_FAILED_{region.center_y}" # 使用坐标作为临时hash
                    }
                    current_page_data.append(placeholder)
            
            # 适度等待，确保剪贴板和UI响应
            time.sleep(0.05) 
            
        # 3. 拼接去重
        new_messages = stitcher.stitch(current_page_data)
        
        if new_messages:
            valid_new_messages = [m for m in new_messages if m['content'] != "<COPY_FAILED>"]
            logger.info(f"本页新增 {len(valid_new_messages)} 条有效消息")
            
            if valid_new_messages:
                no_new_data_count = 0
                for msg in valid_new_messages:
                    # 实时保存
                    save_message_to_jsonl(output_file, msg)
                    preview = msg['content'][:20].replace('\n', ' ')
                    logger.info(f"-> [{msg['sender_type']}] {preview}")
            else:
                # 虽然有新消息，但都是 copy failed
                no_new_data_count += 1
        else:
            no_new_data_count += 1
            logger.info(f"本页无新增数据 ({no_new_data_count}/{max_no_new_limit})")
            
        # 4. 终止条件
        if no_new_data_count >= max_no_new_limit:
            logger.success("已到达底部或无更多内容，任务完成。")
            break
            
        # 5. 小幅向下滚动 (固定距离)
        # 用户反馈：每次滚动太少，导致重复复制过多
        # 增加滚动步长，减少重叠区域，提高效率
        # steps=1 -> 300 units
        # steps=5 -> 1500 units (但实际效果取决于系统缩放和微信行为)
        # 之前的 steps=2 (600) 用户觉得还可以，但现在为了效率，我们尝试 steps=5
        # 如果 steps=5 导致漏消息（无重叠），则需要回调
        logger.info("向下滚动 (Large Step)...")
        automation.scroll_fixed(steps=15) 
        
        # 等待页面稳定
        time.sleep(0.8)

if __name__ == "__main__":
    main()
