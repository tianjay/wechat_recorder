import uiautomation as auto
import pyautogui
from PIL import ImageGrab
import time
import math

def analyze_pixels():
    print("Searching for WeChat window...")
    window = auto.WindowControl(searchDepth=1, RegexName="微信.*")
    if not window.Exists(maxSearchSeconds=2):
        print("WeChat window not found.")
        return

    window.SetActive()
    window.SetTopmost(True)
    time.sleep(1) # Wait for animation
    
    rect = window.BoundingRectangle
    print(f"Window Rect: {rect}")
    
    # Capture the window area
    # Note: uiautomation rect is (left, top, right, bottom)
    # PIL ImageGrab expects (left, top, right, bottom) on Windows
    # pyautogui screenshot region is (left, top, width, height)
    
    # Let's use pyautogui for consistency
    region = (rect.left, rect.top, rect.width(), rect.height())
    print(f"Capturing region: {region}")
    
    # Take screenshot
    try:
        img = pyautogui.screenshot(region=region)
        width, height = img.size
        print(f"Screenshot size: {width}x{height}")
        
        # Analyze horizontal line at 50% height to find sidebar split
        mid_y = height // 2
        print(f"\nScanning horizontal line at y={mid_y}...")
        prev_color = None
        transitions = []
        
        # We expect a sidebar on the left (usually gray) and chat area on right (usually light gray)
        # Scan from x=0 to width
        for x in range(0, width, 5):
            color = img.getpixel((x, mid_y))
            if prev_color and color != prev_color:
                # Simple color distance
                diff = sum(abs(c1 - c2) for c1, c2 in zip(color, prev_color))
                if diff > 30: # Significant change
                    transitions.append((x, prev_color, color))
            prev_color = color
            
        print(f"Found {len(transitions)} significant horizontal color transitions.")
        for t in transitions[:5]: # Show first 5
            print(f"  At x={t[0]}: {t[1]} -> {t[2]}")
            
        # Guess sidebar width
        sidebar_width = 0
        if transitions:
            # Usually the first major transition around 200-350px is the sidebar
            for t in transitions:
                if 200 < t[0] < 400:
                    sidebar_width = t[0]
                    break
        
        if sidebar_width == 0:
            print("Could not detect sidebar, assuming 300px default.")
            sidebar_width = 300
        else:
            print(f"Detected Sidebar Width: ~{sidebar_width}px")

        # Now analyze vertical lines in chat area to find avatars
        # Friend avatar (Left): sidebar_width + margin (~40px)
        # Self avatar (Right): width - margin (~40px)
        
        chat_left_x = sidebar_width + 45 # Approximate center of left avatar
        chat_right_x = width - 45        # Approximate center of right avatar
        
        print(f"\nScanning vertical line for Friend Avatars at x={chat_left_x}...")
        bg_color = img.getpixel((chat_left_x, 10)) # Assume top pixel is background?
        print(f"Assumed Background Color: {bg_color}")
        
        avatars = []
        in_avatar = False
        avatar_start_y = 0
        
        # Scan vertical line
        # Skip top header (usually ~60px) and bottom input area (usually ~150px)
        scan_top = 60
        scan_bottom = height - 150
        
        for y in range(scan_top, scan_bottom):
            color = img.getpixel((chat_left_x, y))
            diff = sum(abs(c1 - c2) for c1, c2 in zip(color, bg_color))
            
            is_different = diff > 20 # Tolerance
            
            if is_different and not in_avatar:
                in_avatar = True
                avatar_start_y = y
            elif not is_different and in_avatar:
                in_avatar = False
                avatar_height = y - avatar_start_y
                if 20 < avatar_height < 60: # Valid avatar size constraint
                    avatars.append(('Left', chat_left_x, avatar_start_y + avatar_height//2))
                    
        print(f"Found {len(avatars)} potential Left Avatars.")
        
        print(f"\nScanning vertical line for Self Avatars at x={chat_right_x}...")
        # Assume same background
        
        in_avatar = False
        avatar_start_y = 0
        right_avatars_count = 0
        
        for y in range(scan_top, scan_bottom):
            color = img.getpixel((chat_right_x, y))
            diff = sum(abs(c1 - c2) for c1, c2 in zip(color, bg_color))
            
            is_different = diff > 20
            
            if is_different and not in_avatar:
                in_avatar = True
                avatar_start_y = y
            elif not is_different and in_avatar:
                in_avatar = False
                avatar_height = y - avatar_start_y
                if 20 < avatar_height < 60:
                    avatars.append(('Right', chat_right_x, avatar_start_y + avatar_height//2))
                    right_avatars_count += 1
                    
        print(f"Found {right_avatars_count} potential Right Avatars.")
        
        # Sort by Y
        avatars.sort(key=lambda x: x[2])
        
        print("\nAll Detected Avatars (Y-sorted):")
        for av in avatars:
            print(f"  {av[0]} Avatar at ({av[1]}, {av[2]})")
            
        # Save debug image with marked points
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        # Draw scan lines
        draw.line([(chat_left_x, 0), (chat_left_x, height)], fill="red", width=1)
        draw.line([(chat_right_x, 0), (chat_right_x, height)], fill="blue", width=1)
        
        # Draw points
        for av in avatars:
            color = "red" if av[0] == 'Left' else "blue"
            x, y = av[1], av[2]
            draw.rectangle([x-5, y-5, x+5, y+5], outline=color, width=2)
            
        img.save("debug_layout.png")
        print("Saved debug_layout.png")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_pixels()
