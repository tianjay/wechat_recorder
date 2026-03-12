import uiautomation as auto

def list_windows():
    print("Listing windows...")
    root = auto.GetRootControl()
    for window in root.GetChildren():
        name = window.Name
        classname = window.ClassName
        if "微信" in name or "WeChat" in name or "WeChat" in classname:
            print(f"Found Window: Name='{name}', ClassName='{classname}', Handle={window.NativeWindowHandle}")

if __name__ == "__main__":
    list_windows()
