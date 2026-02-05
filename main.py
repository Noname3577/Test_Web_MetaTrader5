import tkinter as tk
from gui import MT5DataViewer


def main():
    """ฟังก์ชันหลักสำหรับเริ่มโปรแกรม"""
    root = tk.Tk()
    app = MT5DataViewer(root)
    
    print("="*60)
    print("MetaTrader5 Trading Bot System")
    print("="*60)
    print("กลยุทธ์ที่รองรับ:")
    print("  1. MA Crossover - ตัดเส้น MA")
    print("  2. Donchian Breakout - เบรกเอาท์ตามเทรนด์")
    print("  3. Bollinger Bands - Mean Reversion")
    print("  4. RSI Swing - แกว่งตัวตาม RSI")
    print("  5. MACD - MACD Crossover")
    print("  6. ATR Trailing - Trailing Stop")
    print("  7. Supertrend - เทรนด์ + Trailing")
    print("="*60)
    print("โหมดการทำงาน:")
    print("  - DRY_RUN: ทดสอบ ไม่ส่งคำสั่งจริง")
    print("  - MANUAL_CONFIRM: รอคนยืนยันก่อนส่ง")
    print("  - AUTO: ส่งอัตโนมัติ (ระวัง!)")
    print("="*60)
    print("\n✅ โปรแกรมพร้อมทำงาน\n")
    
    root.mainloop()


if __name__ == "__main__":
    main()
