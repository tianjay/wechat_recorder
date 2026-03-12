import uiautomation as auto
from src.core.layout import LayoutAnalyzer
from PIL import ImageDraw
import time
from loguru import logger

def debug_layout():
    logger.add("debug_layout.log")
    
    # 1. Connect to WeChat
    window = auto.WindowControl(searchDepth=1, RegexName="微信.*")
    if not window.Exists(maxSearchSeconds=2):
        logger.error("WeChat window not found")
        return
    
    # 增强的窗口激活逻辑
    try:
        # 尝试直接还原，使用魔术数字 9 (SW_RESTORE) 以避开属性引用错误
        if window.GetWindowPattern().WindowVisualState == auto.WindowVisualState.Minimized:
            logger.info("窗口已最小化，正在还原...")
            window.ShowWindow(9)
    except Exception as e:
        logger.warning(f"窗口状态检查或还原失败: {e}")
        
    if not window.HasKeyboardFocus:
        window.SetFocus()
            
    window.SetActive()
    time.sleep(1)
    
    # 2. Capture and Analyze
    rect = window.BoundingRectangle
    analyzer = LayoutAnalyzer()
    
    # Capture
    img = analyzer.capture_window(rect)
    logger.info(f"Captured image size: {img.size}")
    
    # Detect
    elements = analyzer.find_elements(img)
    logger.info(f"Detected {len(elements)} elements")
    
    # 3. Draw and Save
    draw = ImageDraw.Draw(img)
    width = img.width
    height = img.height
    
    # 获取实际使用的扫描线位置（参考 src/core/layout.py）
    sidebar_width = analyzer.sidebar_width
    left_scan_x = sidebar_width + 45
    right_scan_x = width - 60
    center_scan_x = sidebar_width + (width - sidebar_width) // 2
    
    # 绘制扫描线
    draw.line((left_scan_x, 0, left_scan_x, height), fill="blue", width=2) # 左侧扫描线
    draw.line((right_scan_x, 0, right_scan_x, height), fill="green", width=2) # 右侧扫描线
    draw.line((center_scan_x, 0, center_scan_x, height), fill="yellow", width=2) # 中间时间戳扫描线
    draw.line((sidebar_width, 0, sidebar_width, height), fill="gray", width=2) # 侧边栏分界线

    # 绘制图例
    draw.text((10, 10), "Blue: Left Scan | Green: Right Scan | Yellow: Time Scan", fill="red")

    for i, e in enumerate(elements):
        logger.info(f"Element {i}: Type={e.type}, Center=({e.center_x}, {e.center_y}), Height={e.height}")
        
        # 绘制检测到的元素中心点
        r = 5
        color = "red"
        if e.type == 'Left': color = "blue"
        elif e.type == 'Right': color = "green"
        elif e.type == 'Time': color = "yellow"
        
        # 画圆点表示点击位置
        draw.ellipse((e.center_x - r, e.center_y - r, e.center_x + r, e.center_y + r), fill=color, outline="black")
        
        # 标注序号和类型
        text = f"#{i} {e.type}"
        # 文本偏移一点避免遮挡
        text_x = e.center_x + 10
        if e.type == 'Right': text_x = e.center_x - 60
        draw.text((text_x, e.center_y - 10), text, fill="red")
        
        # 绘制水平辅助线，验证垂直排序
        draw.line((0, e.center_y, width, e.center_y), fill="red", width=1)

    output_path = "debug_layout_result.png"
    img.save(output_path)
    logger.info(f"Saved debug image to {output_path}")

if __name__ == "__main__":
    debug_layout()
