import pyperclip
import time

def test_clipboard():
    print("Testing clipboard...")
    try:
        pyperclip.copy("Hello World")
        time.sleep(0.5)
        content = pyperclip.paste()
        print(f"Clipboard content: '{content}'")
        if content == "Hello World":
            print("Clipboard works!")
        else:
            print("Clipboard mismatch.")
    except Exception as e:
        print(f"Clipboard error: {e}")

if __name__ == "__main__":
    test_clipboard()
