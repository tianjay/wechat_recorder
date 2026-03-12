import uiautomation as auto
import time
from src.core.layout import LayoutAnalyzer
from PIL import ImageDraw

def test_scan():
    print("Connecting to WeChat...")
    win = auto.WindowControl(searchDepth=1, RegexName="微信.*")
    if not win.Exists(maxSearchSeconds=2):
        print("Not found")
        return
        
    win.SetActive()
    time.sleep(1)
    
    rect = win.BoundingRectangle
    print(f"Window: {rect}")
    
    analyzer = LayoutAnalyzer()
    img = analyzer.capture_window(rect)
    
    print("Analyzing layout...")
    analyzer.detect_layout_structure(img)
    
    print("Finding messages...")
    msgs = analyzer.find_avatars(img)
    
    print(f"Found {len(msgs)} messages.")
    
    draw = ImageDraw.Draw(img)
    for m in msgs:
        print(f"  {m.type} at ({m.center_x}, {m.center_y}) h={m.height}")
        # Draw target point
        x, y = m.center_x, m.center_y
        draw.ellipse([x-5, y-5, x+5, y+5], fill='red' if m.type=='Left' else 'blue')
        
    img.save("debug_scan_result.png")
    print("Saved debug_scan_result.png")

if __name__ == "__main__":
    test_scan()
