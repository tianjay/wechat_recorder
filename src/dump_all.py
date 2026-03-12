import uiautomation as auto
import sys

def dump_all():
    print("Searching for WeChat window...")
    window = auto.WindowControl(searchDepth=1, RegexName="微信.*")
    if not window.Exists(maxSearchSeconds=2):
        print("WeChat window not found.")
        return

    print(f"Found Window: {window.Name} ({window.ClassName})")
    print("Dumping entire tree to tree.txt...")
    
    with open("tree.txt", "w", encoding="utf-8") as f:
        def walker(control, depth):
            indent = "  " * depth
            try:
                info = f"{indent}[{control.ControlTypeName}] Name='{control.Name}' ClassName='{control.ClassName}' Rect={control.BoundingRectangle}"
                f.write(info + "\n")
                # Limit depth to avoid infinite recursion or too large files
                if depth < 10:
                    children = control.GetChildren()
                    for child in children:
                        walker(child, depth + 1)
            except Exception as e:
                f.write(f"{indent}Error: {e}\n")

        walker(window, 0)
    
    print("Dump complete. Check tree.txt")

if __name__ == "__main__":
    dump_all()
