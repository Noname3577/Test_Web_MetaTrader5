import tkinter as tk
from gui import MT5DataViewer


def main():
    """ฟังก์ชันหลักสำหรับเริ่มโปรแกรม"""
    root = tk.Tk()
    app = MT5DataViewer(root)
    print("\n✅ โปรแกรมพร้อมทำงาน\n")
    
    root.mainloop()


if __name__ == "__main__":
    main()
