import uiautomation as auto
import time
import random
import pyperclip
import pyautogui
import hashlib
from typing import List, Optional, Tuple, Dict
from loguru import logger
from src.core.layout import LayoutAnalyzer, MessageRegion

class WeChatAutomation:
    def __init__(self):
        self.window = auto.WindowControl(searchDepth=1, RegexName="微信.*")
        self.layout_analyzer = LayoutAnalyzer()
        self.message_list = None
        
    def connect(self) -> bool:
        """连接到微信窗口"""
        if not self.window.Exists(maxSearchSeconds=2):
            logger.error("未找到微信窗口，请确保微信已登录并打开")
            return False
            
        # 优化窗口激活逻辑：
        # 1. 如果窗口最小化，则还原
        # 2. 如果窗口正常或最大化，则直接聚焦，避免改变大小
        try:
            # CurrentWindowVisualState 是一个属性，不是方法
            # uiautomation 2.0+
            current_state = self.window.GetWindowPattern().WindowVisualState
            # WindowVisualState.Minimized 也是一个值
            if current_state == auto.WindowVisualState.Minimized:
                logger.info("窗口已最小化，正在还原...")
                # ShowWindow 是一个函数，参数是常量
                # 使用魔术数字 9 (SW_RESTORE) 以避开属性引用错误
                self.window.ShowWindow(9)
        except Exception as e:
            logger.warning(f"获取窗口状态失败，尝试直接激活: {e}")
            
        # HasKeyboardFocus 是一个属性，不是方法
        if not self.window.HasKeyboardFocus:
             self.window.SetFocus()
        
        self.window.SetActive()
        # 移除 SetTopmost(True)，防止强制置顶导致的不便或窗口行为异常
        # self.window.SetTopmost(True)
        time.sleep(0.5)
        return True

    def get_message_area_rect(self):
        """获取窗口位置信息"""
        return self.window.BoundingRectangle

    def scan_messages(self) -> List[MessageRegion]:
        """扫描当前可见的消息位置"""
        rect = self.get_message_area_rect()
        img = self.layout_analyzer.capture_window(rect)
        messages = self.layout_analyzer.find_elements(img)
        
        # 将相对坐标转换为屏幕绝对坐标，并计算点击位置偏移
        abs_messages = []
        for msg in messages:
            # 计算点击偏移量：从头像中心移动到消息气泡内
            # 头像宽度约 40px，间隙约 10px，气泡内边距约 10px
            # 安全偏移量：40/2 + 10 + 20 = 50px 左右
            # 左侧好友：向右偏移
            # 右侧自己：向左偏移
            offset_x = 0
            if msg.type == 'Left':
                offset_x = 45 # 向右偏移 60px
            elif msg.type == 'Right':
                offset_x = -45 # 向左偏移 60px
            
            abs_msg = MessageRegion(
                type=msg.type,
                center_x=msg.center_x + rect.left + offset_x, # 应用偏移
                center_y=msg.center_y + rect.top,
                height=msg.height,
                bbox=msg.bbox # bbox 保持原始（相对于窗口），或者不需要转换
            )
            # 注意：这里的 bbox 是相对于截图的，如果后续需要用到绝对坐标的 bbox，也需要转换
            # 但目前 automation 中只用 center_x/y 点击，所以只转换 center 即可
            
            abs_messages.append(abs_msg)
            
        # Debug: 标注并保存截图
        try:
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            width = img.width
            height = img.height
            
            # 绘制扫描线
            # 注意：这里必须与 layout.py 中的逻辑完全一致
            sidebar_width = self.layout_analyzer.sidebar_width
            
            for i, msg in enumerate(messages):
                # 绘制原始头像位置
                # r = 5
                color = "red"
                if msg.type == 'Left': color = "blue"
                elif msg.type == 'Right': color = "green"
                elif msg.type == 'Time': color = "yellow"
                
                # 绘制头像边框 (如果有)
                if msg.bbox:
                    x, y, w, h = msg.bbox
                    draw.rectangle([x, y, x+w, y+h], outline=color, width=2)
                
                # 计算并绘制实际点击位置 (Debug 图像上需要模拟偏移)
                offset_x = 0
                if msg.type == 'Left': offset_x = 60
                elif msg.type == 'Right': offset_x = -60
                
                click_x = msg.center_x + offset_x
                click_y = msg.center_y
                
                # 绘制点击点 (实心圆)
                draw.ellipse((click_x - 5, click_y - 5, click_x + 5, click_y + 5), fill=color, outline="white")
                draw.text((click_x + 10, click_y - 10), f"#{i} Click", fill="red")
                
            # 保存到 logs 目录，带时间戳
            import os
            os.makedirs("logs/debug_scans", exist_ok=True)
            timestamp = int(time.time() * 1000)
            img.save(f"logs/debug_scans/scan_{timestamp}.png")
            logger.info(f"Debug scan saved to logs/debug_scans/scan_{timestamp}.png")
            
        except Exception as e:
            logger.warning(f"Failed to save debug scan image: {e}")

        return abs_messages

    def click_and_copy(self, x: int, y: int, is_retry: bool = False) -> Optional[str]:
        """点击指定位置并尝试复制"""
        try:
            # 用户明确要求：必须双击才能全选然后复制
            # 策略调整：直接使用双击 + Ctrl+C
            pyautogui.moveTo(x, y)
            
            # 双击以全选/选中
            pyautogui.doubleClick(x, y)
            time.sleep(0.3) # 等待选中生效或窗口响应
            
            # 清空剪贴板
            pyperclip.copy("") 
            
            # 尝试复制
            pyautogui.hotkey('ctrl', 'c')
            
            # 等待剪贴板更新
            for _ in range(5): # 稍微增加重试次数，因为双击可能需要更多反应时间
                time.sleep(0.1)
                content = pyperclip.paste()
                if content:
                    return content.strip()
            
            # 如果复制失败，可能是因为双击打开了图片/文件预览窗口
            # 或者是无法复制的内容
            logger.debug(f"双击复制失败，剪贴板为空: ({x}, {y})")
            
            # 可选：尝试按 ESC 关闭可能打开的预览窗口？
            # pyautogui.press('esc')
            
            return None
                
        except Exception as e:
            logger.error(f"Error in click_and_copy: {e}")
            
        return None

    # def _handle_voice_message(self, x: int, y: int) -> Optional[str]:
    #     """尝试处理语音消息：右键 -> 语音转文字 -> 抓取下方文本"""
    #     logger.info(f"尝试处理可能的语音消息: ({x}, {y})")
        
    #     # 1. 右键点击
    #     pyautogui.rightClick(x, y)
    #     time.sleep(0.5)
        
    #     # 2. 查找菜单项 "语音转文字"
    #     menu_item = auto.MenuItemControl(Name="语音转文字", searchDepth=5)
        
    #     # 有时候菜单是 List/ListItem，或者 Pane/Text
    #     if not menu_item.Exists(maxSearchSeconds=1):
    #          # 尝试 TextControl，有时 UI 结构不同
    #          menu_item = auto.TextControl(Name="语音转文字", searchDepth=5)
        
    #     if menu_item.Exists(maxSearchSeconds=1):
    #         logger.info("找到'语音转文字'选项，点击...")
    #         menu_item.Click()
            
    #         # 等待转换（网络请求）
    #         time.sleep(2.0) 
            
    #         # 3. 向下移动并复制
    #         # 用户说 "向下挪动鼠标一个消息气泡的距离"
    #         # 假设这个距离是 80px
    #         new_y = y + 80
            
    #         logger.info(f"移动到下方抓取转换后的文本: ({x}, {new_y})")
    #         return self.click_and_copy(x, new_y, is_retry=True)
    #     else:
    #         logger.warning("未找到'语音转文字'菜单，可能不是语音消息或菜单不可见")
    #         # 关闭菜单 (点击别处)
    #         pyautogui.click(x - 50, y) 
    #         return None

    def _get_visual_state(self):
        """获取当前消息区域的视觉状态哈希"""
        rect = self.get_message_area_rect()
        img = self.layout_analyzer.capture_window(rect)
        # 缩小图片以忽略细微差异并加速
        small = img.resize((100, 100))
        return hashlib.md5(small.tobytes()).hexdigest()

    def scroll_to_top(self, max_attempts=50):
        """滚动到顶部，直到内容不再变化"""
        logger.info("开始尝试滚动到顶部...")
        
        # 先确保激活窗口
        rect = self.get_message_area_rect()
        x = rect.left + rect.width() // 2
        y = rect.top + rect.height() // 2
        pyautogui.moveTo(x, y)
        pyautogui.click()
        
        # 策略 1: 尝试使用 Home 键 (极速置顶)
        logger.info("尝试使用 Home 键快速置顶...")
        pyautogui.press('home')
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'home') # 有些列表需要 Ctrl+Home
        time.sleep(0.5)
        
        # 策略 2: 滚轮辅助确认
        logger.info("使用滚轮辅助确认并微调...")
        
        last_state = None
        unchanged_count = 0
        
        for i in range(max_attempts):
            current_state = self._get_visual_state()
            
            if current_state == last_state:
                unchanged_count += 1
                if unchanged_count >= 2: # 连续2次无变化即可确认，提高速度
                    logger.success("视觉状态稳定，确认已到达顶部")
                    break
            else:
                unchanged_count = 0
            
            last_state = current_state
            
            # 使用大幅滚动，加速置顶
            # 连续发送多次滚动指令，减少等待
            for _ in range(10): # 增加滚动次数
                pyautogui.scroll(10000) 
            
            time.sleep(0.1) # 减少等待时间
            
            if i % 5 == 0:
                logger.info(f"正在向上滚动... ({i}/{max_attempts})")

    def scroll_up(self, steps: int = 5):
        """向上滚动"""
        rect = self.get_message_area_rect()
        # 鼠标放在消息区域中间
        x = rect.left + rect.width() // 2
        y = rect.top + rect.height() // 2
        
        pyautogui.moveTo(x, y)
        pyautogui.click() # 激活焦点
        
        for _ in range(steps):
            pyautogui.scroll(300)
            time.sleep(0.1)

    def scroll_fixed(self, steps: int = 3):
        """向下滚动固定距离（小步慢跑，确保重叠）"""
        rect = self.get_message_area_rect()
        x = rect.left + rect.width() // 2
        y = rect.top + rect.height() // 2
        
        pyautogui.moveTo(x, y)
        
        # 每次滚动 -100 单位，通常是 1-3 行的高度
        for _ in range(steps):
            pyautogui.scroll(-300) 
            time.sleep(0.05)

    def scroll_page_down(self):
        """向下滚动大约一页"""
        rect = self.get_message_area_rect()
        x = rect.left + rect.width() // 2
        y = rect.top + rect.height() // 2
        
        pyautogui.moveTo(x, y)
        pyautogui.click()
        
        # 尝试使用 PageDown 键，通常比滚轮更可靠地滚动一页
        # 但有些时候 PageDown 可能不生效，取决于焦点
        # 这里使用滚轮模拟大幅滚动，大约 70% 屏幕高度
        # 假设每次 scroll(100) 大约滚动 30-50 像素
        # 1200px 屏幕 -> 800px -> ~20 clicks
        steps = 15 
        for _ in range(steps):
            pyautogui.scroll(-300)
            time.sleep(0.02)
        # 移除内部等待，由外部控制
