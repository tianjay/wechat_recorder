import os
import time
import numpy as np
import pyautogui
import cv2
from PIL import Image
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from loguru import logger
from collections import Counter

@dataclass
class MessageRegion:
    type: str  # 'Left', 'Right', 'Time'
    center_x: int
    center_y: int
    height: int
    # 新增：记录头像的边界框，用于调试绘制
    bbox: Optional[Tuple[int, int, int, int]] = None  # (x, y, w, h)

class LayoutAnalyzer:
    def __init__(self):
        self.sidebar_width = 270 
        self.bg_color = None
        self.friend_avatar_right = 0
        self.self_avatar_left = 0
        self.debug_mode = True # 开启调试模式以保存中间图像

    def capture_window(self, rect) -> Image.Image:
        """Capture the window content."""
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        return pyautogui.screenshot(region=(rect.left, rect.top, width, height))

    def detect_layout_structure(self, img: Image.Image):
        """Analyze screenshot to find sidebar width and background color."""
        arr = np.array(img)
        height, width, _ = arr.shape
        
        # 1. Detect Sidebar using Canny
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 30, 100)
        col_sums = np.sum(edges, axis=0)
        
        # Search sidebar
        search_start = 220
        search_end = 600
        if search_end > width: search_end = width - 10
        roi = col_sums[search_start:search_end]
        if len(roi) > 0:
            peak_idx = np.argmax(roi)
            if roi[peak_idx] > height * 0.3 * 255:
                self.sidebar_width = search_start + peak_idx + 5
                logger.info(f"Detected sidebar width (Canny): {self.sidebar_width}")
            else:
                 # Fallback
                 logger.warning(f"Canny peak low ({roi[peak_idx]}), using default 300")
                 self.sidebar_width = 300
        else:
            self.sidebar_width = 300
            
        # 2. Detect Background Color
        chat_x_start = self.sidebar_width + 20
        chat_x_end = width - 20
        if chat_x_start >= chat_x_end: chat_x_start = self.sidebar_width + 5
        
        sample_region = arr[60:height-100, chat_x_start:chat_x_end]
        pixels = sample_region.reshape(-1, 3)
        pixels_sub = pixels[::100]
        pixels_tuples = [tuple(p) for p in pixels_sub]
        if pixels_tuples:
            common = Counter(pixels_tuples).most_common(1)
            self.bg_color = np.array(common[0][0])
        else:
            self.bg_color = np.array([245, 245, 245])

    def find_elements(self, img: Image.Image) -> List[MessageRegion]:
        """使用 OpenCV 轮廓检测来识别头像"""
        if self.bg_color is None:
            self.detect_layout_structure(img)
            
        arr = np.array(img)
        height, width, _ = arr.shape
        
        # 定义搜索区域
        # 左侧头像区域：侧边栏右侧附近
        left_region_x_min = self.sidebar_width + 5
        left_region_x_max = self.sidebar_width + 80 # 头像一般在这个范围内
        
        # 右侧头像区域：窗口右侧附近
        right_region_x_min = width - 80
        right_region_x_max = width - 5
        
        logger.debug(f"Search regions: Left={left_region_x_min}-{left_region_x_max}, Right={right_region_x_min}-{right_region_x_max}")
        
        messages = []
        
        # 辅助函数：在指定区域查找头像
        def process_region(x_min, x_max, region_type):
            if x_min >= x_max or x_min < 0 or x_max > width:
                return
                
            roi = arr[:, x_min:x_max]
            # 计算 ROI 内的差异
            diff = np.mean(np.abs(roi - self.bg_color), axis=2)
            
            # 二值化
            _, binary = cv2.threshold(diff.astype(np.uint8), 10, 255, cv2.THRESH_BINARY)
            
            # 形态学操作
            kernel = np.ones((3,3), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # 查找轮廓
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 保存 ROI 调试图像
            if self.debug_mode:
                try:
                    os.makedirs("logs/debug_cv", exist_ok=True)
                    ts = int(time.time())
                    cv2.imwrite(f"logs/debug_cv/{region_type}_binary_{ts}.png", binary)
                except Exception as e:
                    logger.warning(f"Failed to save debug cv images: {e}")

            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                
                # 转换回全局坐标
                global_x = x_min + x
                global_y = y
                
                # 1. 尺寸过滤
                MIN_SIZE = 25 # 放宽下限，避免漏掉
                MAX_SIZE = 70 # 头像通常是 35-45 左右
                
                if not (MIN_SIZE < w < MAX_SIZE and MIN_SIZE < h < MAX_SIZE):
                    continue
                    
                # 2. 比例过滤
                aspect_ratio = float(w) / h
                if not (0.7 < aspect_ratio < 1.3):
                    continue
                
                center_x = global_x + w // 2
                center_y = global_y + h // 2
                
                # 排除顶部和底部
                if center_y < 60 or center_y > height - 60:
                    continue
                    
                messages.append(MessageRegion(
                    type=region_type,
                    center_x=center_x,
                    center_y=center_y,
                    height=h,
                    bbox=(global_x, global_y, w, h)
                ))

        # 分别处理左右区域
        process_region(left_region_x_min, left_region_x_max, 'Left')
        process_region(right_region_x_min, right_region_x_max, 'Right')
        
        logger.info(f"Found {len(messages)} avatar candidates")
        
        # 2. 识别时间戳 (Center Strip)
        # 扫描中心区域的一个条带，而不仅仅是一列
        center_scan_x = self.sidebar_width + (width - self.sidebar_width) // 2
        strip_width = 10
        strip_x_start = max(0, center_scan_x - strip_width // 2)
        strip_x_end = min(width, center_scan_x + strip_width // 2)
        
        strip = arr[60:height-120, strip_x_start:strip_x_end]
        
        # 计算每一行的差异
        # 1. 计算每个像素与背景的差异 -> (H, W)
        diff_strip = np.mean(np.abs(strip - self.bg_color), axis=2)
        
        # 2. 取每一行的最大差异值 -> (H,)
        # 只要该行有任何像素不同于背景，就认为是活跃行
        row_max_diff = np.max(diff_strip, axis=1)
        
        is_active = row_max_diff > 10 # 稍微提高阈值以过滤噪声
        
        # 收集头像的 Y 范围，用于过滤
        avatar_y_ranges = []
        for msg in messages:
            # 扩大一点范围，避免时间戳紧贴头像
            avatar_y_ranges.append((msg.center_y - msg.height - 10, msg.center_y + msg.height + 10))
            
        # 扫描时间戳
        in_blob = False
        start_y = 0
        scan_top = 60
        
        for i, active in enumerate(is_active):
            actual_y = scan_top + i
            if active and not in_blob:
                in_blob = True
                start_y = actual_y
            elif not active and in_blob:
                in_blob = False
                h = actual_y - start_y
                if h > 10 and h < 50: # 时间戳通常比较矮
                    # 检查是否与头像重叠
                    center_y = start_y + h // 2
                    is_overlap = False
                    for a_start, a_end in avatar_y_ranges:
                        if not (actual_y < a_start or start_y > a_end):
                            is_overlap = True
                            break
                    
                    if not is_overlap:
                        messages.append(MessageRegion(
                            type='Time',
                            center_x=center_scan_x,
                            center_y=center_y,
                            height=h,
                            bbox=None
                        ))

        # Sort all by Y
        messages.sort(key=lambda m: m.center_y)
        return messages

if __name__ == "__main__":
    pass
