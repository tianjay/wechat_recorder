import uiautomation as auto
import sys

def dump_tree():
    print("Searching for WeChat window...")
    window = auto.WindowControl(searchDepth=1, RegexName="微信.*")
    if not window.Exists(maxSearchSeconds=2):
        print("WeChat window not found.")
        return

    print(f"Found Window: {window.Name} ({window.ClassName})")
    print("Dumping children (Depth 2)...")
    
    # 遍历打印前 2 层子控件
    for child in window.GetChildren():
        print(f"  [{child.ControlTypeName}] Name='{child.Name}' ClassName='{child.ClassName}' Rect={child.BoundingRectangle}")
        try:
            for grand_child in child.GetChildren():
                print(f"    [{grand_child.ControlTypeName}] Name='{grand_child.Name}' ClassName='{grand_child.ClassName}' Rect={grand_child.BoundingRectangle}")
        except Exception:
            pass

if __name__ == "__main__":
    dump_tree()
