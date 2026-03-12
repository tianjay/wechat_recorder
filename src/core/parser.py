from typing import Dict, Any
import uiautomation as auto
from loguru import logger

class MessageParser:
    def parse(self, item: auto.ListItemControl) -> Dict[str, Any]:
        """
        解析单条消息
        返回结构:
        {
            "type": "text" | "image" | "file" | "system" | "unknown",
            "sender": str,
            "time": str, # 并不是每条消息都有时间，可能需要上下文推断
            "content": str,
            "raw_text": str
        }
        """
        # 获取消息项的完整文本
        # 微信的消息项通常包含：头像、昵称、消息内容、时间
        # Name 属性通常包含了所有文本信息
        raw_name = item.Name
        
        # 简单的类型判断
        msg_type = "text"
        content = raw_name
        
        # 尝试查找更详细的结构
        # 微信的消息结构通常是：
        # ListItem
        #   Pane (头像)
        #   Pane (内容区域)
        #     Text (昵称)
        #     Text (内容) / Image / Button (文件)
        
        children = item.GetChildren()
        
        # 这是一个非常基础的解析，实际微信结构可能很复杂
        # 需要根据实际调试结果来优化
        
        if "[图片]" in raw_name:
            msg_type = "image"
        elif "[文件]" in raw_name:
            msg_type = "file"
        elif "撤回了一条消息" in raw_name:
            msg_type = "system"
            
        return {
            "type": msg_type,
            "content": content,
            "raw_text": raw_name,
            "sender": "Unknown" # 需要进一步解析
        }
