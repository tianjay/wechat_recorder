import uiautomation as auto
import time
import pyautogui

def test_home_key():
    print("Connecting to WeChat...")
    win = auto.WindowControl(searchDepth=1, RegexName="微信.*")
    if not win.Exists(maxSearchSeconds=2):
        print("Not found")
        return
        
    win.SetActive()
    time.sleep(1)
    
    # 获取消息区域中心
    rect = win.BoundingRectangle
    x = rect.left + rect.width() // 2
    y = rect.top + rect.height() // 2
    
    print("Clicking center...")
    pyautogui.click(x, y)
    
    print("Testing 'Home' key...")
    pyautogui.press('home')
    
    print("Testing 'Ctrl+Home' key...")
    pyautogui.hotkey('ctrl', 'home')
    
    print("Done. Please check if it scrolled to top.")

if __name__ == "__main__":
    test_home_key()
