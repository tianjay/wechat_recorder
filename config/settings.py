"""
配置文件 - 微信聊天记录读取器设置
"""

import os
from pathlib import Path
from typing import Dict, Any


class Settings:
    """应用程序设置"""
    
    def __init__(self):
        # 基础配置
        self.output_dir = Path(os.getenv('OUTPUT_DIR', 'recorded_data'))
        self.screenshot_interval = float(os.getenv('SCREENSHOT_INTERVAL', '1.0'))
        self.ocr_language = os.getenv('OCR_LANGUAGE', 'chi_sim+eng')
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        
        # 窗口识别配置
        self.wechat_window_title = os.getenv('WECHAT_WINDOW_TITLE', '微信')
        
        # 调试模式
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        
        # 创建输出目录
        self.output_dir.mkdir(exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """将设置转换为字典"""
        return {
            'output_dir': str(self.output_dir),
            'screenshot_interval': self.screenshot_interval,
            'ocr_language': self.ocr_language,
            'max_retries': self.max_retries,
            'wechat_window_title': self.wechat_window_title,
            'debug': self.debug
        }


# 全局配置实例
settings = Settings()