"""
GUI Module - อัปเดตเพื่อรองรับระบบเทรดอัตโนมัติ
ส่วนติดต่อผู้ใช้สำหรับแสดงข้อมูล MT5 และควบคุม Trading Bot
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional, Dict, List, Any
import numpy as np

from mt5_handler import MT5Handler
from signal_engine import SignalEngine, TradingSignal
from risk_manager import RiskManager
from execution_engine import ExecutionEngine
from config import ExecutionMode, StrategyType, set_execution_mode, get_execution_mode
from chart_visualizer import ChartVisualizer


class MT5DataViewer:
    """คลาสสำหรับแสดงข้อมูล MT5 ผ่าน GUI พร้อมระบบเทรดอัตโนมัติ"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("MetaTrader5 Trading Bot System - Unified Dashboard")
        self.root.geometry("1400x900")
        
        # สร้าง MT5 Handler
        self.mt5_handler = MT5Handler()
        
        # สร้าง Trading Engines
        self.signal_engine = SignalEngine()
        self.risk_manager = RiskManager()
        self.exec_engine = None  # จะสร้างหลังจากเชื่อมต่อ MT5

        # ตัวแปรสำหรับการอัปเดตแบบ Real-time
        self.refresh_job = None
        self.last_view = None
        self.auto_refresh_var = tk.BooleanVar(value=False)
        self.refresh_interval_var = tk.IntVar(value=2)
        
        # Real-time Account Update
        self.account_auto_refresh = tk.BooleanVar(value=True)
        self.account_refresh_job = None
        
        # ตัวแปรสำหรับระบบเทรด
        self.bot_running = tk.BooleanVar(value=False)
        self.selected_strategy = tk.StringVar(value=StrategyType.MA_CROSSOVER.value)
        self.selected_mode = tk.StringVar(value=ExecutionMode.DRY_RUN.value)
        
        # Chart Visualizer
        self.chart_visualizer = None
        self.chart_auto_refresh = tk.BooleanVar(value=True)
        self.chart_refresh_job = None
        
        # สร้าง UI
        self.create_widgets()
    
    def create_widgets(self):
        """สร้าง UI Components"""
        # สร้าง Notebook สำหรับแท็บต่างๆ
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # แท็บ 1: MT5 Connection & Data
        self.tab_mt5 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_mt5, text="🔌 MT5 Data")
        self._create_mt5_tab()
        
        # แท็บ 2: Trading Dashboard (รวม Bot + Chart + Orders)
        self.tab_dashboard = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dashboard, text="📊 Trading Dashboard")
        self._create_dashboard_tab()
        
        # แท็บ 3: Risk & Stats
        self.tab_stats = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_stats, text="📈 Stats & Risk")
        self._create_stats_tab()
    
    def _create_mt5_tab(self):
        """สร้างแท็บ MT5 Data (เหมือนเดิม)"""
        self._create_connection_frame(self.tab_mt5)
        self._create_account_frame(self.tab_mt5)
        self._create_symbol_frame(self.tab_mt5)
        self._create_data_frame(self.tab_mt5)
    
    def _create_dashboard_tab(self):
        """สร้างแท็บ Dashboard รวม Bot + Chart + Orders"""
        # สร้าง PanedWindow สำหรับแบ่งพื้นที่
        main_paned = ttk.PanedWindow(self.tab_dashboard, orient=tk.HORIZONTAL)
        main_paned.pack(fill="both", expand=True, padx=5, pady=5)
        
        # ส่วนซ้าย: Bot Controls + Log (30%)
        left_frame = ttk.Frame(main_paned, width=350)
        main_paned.add(left_frame, weight=1)
        
        # ส่วนขวา: Chart + Orders (70%)
        right_paned = ttk.PanedWindow(main_paned, orient=tk.VERTICAL)
        main_paned.add(right_paned, weight=2)
        
        # === ส่วนซ้าย: Bot Controls ===
        self._create_bot_control_panel(left_frame)
        
        # === ส่วนขวาบน: Live Chart (60%) ===
        chart_frame = ttk.LabelFrame(right_paned, text="📈 Live Chart", padding=5)
        right_paned.add(chart_frame, weight=3)
        self._create_chart_panel(chart_frame)
        
        # === ส่วนขวาล่าง: Pending Orders (40%) ===
        orders_frame = ttk.LabelFrame(right_paned, text="📋 Pending Orders", padding=5)
        right_paned.add(orders_frame, weight=2)
        self._create_orders_panel(orders_frame)
    
    def _create_bot_control_panel(self, parent):
        """สร้างแผงควบคุม Bot"""
        # ส่วนควบคุมหลัก
        control_frame = ttk.LabelFrame(parent, text="⚙️ การควบคุม Bot", padding=10)
    def _create_bot_control_panel(self, parent):
        """สร้างแผงควบคุม Bot"""
        # ส่วนควบคุมหลัก
        control_frame = ttk.LabelFrame(parent, text="⚙️ การควบคุม Bot", padding=10)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # เลือกโหมด
        ttk.Label(control_frame, text="โหมด:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        mode_combo = ttk.Combobox(control_frame, textvariable=self.selected_mode, 
                                  values=[m.value for m in ExecutionMode], state="readonly", width=18)
        mode_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        # เลือกกลยุทธ์
        ttk.Label(control_frame, text="กลยุทธ์:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        strategy_combo = ttk.Combobox(control_frame, textvariable=self.selected_strategy,
                                     values=[s.value for s in StrategyType], state="readonly", width=18)
        strategy_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # เลือกสัญลักษณ์
        ttk.Label(control_frame, text="สัญลักษณ์:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.bot_symbol_var = tk.StringVar(value="EURUSD")
        symbol_entry = ttk.Entry(control_frame, textvariable=self.bot_symbol_var, width=20)
        symbol_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        control_frame.columnconfigure(1, weight=1)
        
        # ปุ่มควบคุม
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.start_bot_btn = ttk.Button(btn_frame, text="▶ เริ่ม", 
                                        command=self.start_bot, state="disabled", width=10)
        self.start_bot_btn.pack(side="left", padx=3)
        
        self.stop_bot_btn = ttk.Button(btn_frame, text="⏹ หยุด",
                                       command=self.stop_bot, state="disabled", width=10)
        self.stop_bot_btn.pack(side="left", padx=3)
        
        self.scan_btn = ttk.Button(btn_frame, text="🔍 สแกน",
                                   command=self.manual_scan, state="disabled", width=10)
        self.scan_btn.pack(side="left", padx=3)
        
        # สถานะ Bot
        status_frame = ttk.LabelFrame(parent, text="📊 สถานะ", padding=10)
        status_frame.pack(fill="x", padx=5, pady=5)
        
        self.bot_status_label = ttk.Label(status_frame, text="สถานะ: ปิด", 
                                         foreground="gray", font=("Arial", 9, "bold"))
        self.bot_status_label.pack()
        
        # Quick Stats
        quick_stats_frame = ttk.LabelFrame(parent, text="📈 Quick Stats", padding=10)
        quick_stats_frame.pack(fill="x", padx=5, pady=5)
        
        self.quick_stats_text = tk.Text(quick_stats_frame, height=8, wrap=tk.WORD, 
                                        font=("Courier New", 9))
        self.quick_stats_text.pack(fill="x")
        self._update_quick_stats()
        
        # Log
        log_frame = ttk.LabelFrame(parent, text="📝 Log", padding=5)
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.bot_log = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD,
                                                 font=("Courier New", 8))
        self.bot_log.pack(fill="both", expand=True)
    
    def _create_chart_panel(self, parent):
        """สร้างแผงกราฟ"""
        # ส่วนควบคุมด้านบน
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(control_frame, text="Symbol:").pack(side="left", padx=5)
        self.chart_symbol_var = tk.StringVar(value="EURUSD")
        symbol_entry = ttk.Entry(control_frame, textvariable=self.chart_symbol_var, width=12)
        symbol_entry.pack(side="left", padx=5)
        
        # ซิงค์กับ bot symbol
        ttk.Button(control_frame, text="⇄ ซิงค์", 
                  command=self.sync_chart_symbol, width=8).pack(side="left", padx=2)
        
        ttk.Label(control_frame, text="Strategy:").pack(side="left", padx=5)
        self.chart_strategy_var = tk.StringVar(value=StrategyType.MA_CROSSOVER.value)
        strategy_combo = ttk.Combobox(control_frame, textvariable=self.chart_strategy_var,
                                     values=[s.value for s in StrategyType], 
                                     state="readonly", width=18)
        strategy_combo.pack(side="left", padx=5)
        
        ttk.Button(control_frame, text="📊 อัปเดต", 
                  command=self.update_chart_now, width=10).pack(side="left", padx=5)
        
        ttk.Checkbutton(control_frame, text="Auto (5s)", 
                       variable=self.chart_auto_refresh,
                       command=self.toggle_chart_refresh).pack(side="left", padx=5)
        
        # สถานะ
        self.chart_status_label = ttk.Label(control_frame, text="", foreground="gray",
                                           font=("Arial", 8))
        self.chart_status_label.pack(side="left", padx=10)
        
        # พื้นที่สำหรับกราฟ
        self.chart_container = ttk.Frame(parent)
        self.chart_container.pack(fill="both", expand=True, padx=2, pady=2)
    
    def _create_orders_panel(self, parent):
        """สร้างแผงแสดง Pending Orders"""
        # คำอธิบาย
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill="x", padx=5, pady=3)
        
        ttk.Label(info_frame, text="คำสั่งที่รอยืนยัน (โหมด MANUAL_CONFIRM)",
                 font=("Arial", 9)).pack(side="left")
        
        # ปุ่มควบคุมด้านขวา
        btn_frame = ttk.Frame(info_frame)
        btn_frame.pack(side="right")
        
        ttk.Button(btn_frame, text="✅ อนุมัติ", command=self.approve_ticket,
                  width=10).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="❌ ปฏิเสธ", command=self.reject_ticket,
                  width=10).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🔄 รีเฟรช", command=self.refresh_tickets,
                  width=10).pack(side="left", padx=2)
        
        # Treeview สำหรับแสดงตั๋ว
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=3)
        
        # Scrollbar
        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical")
        scrollbar_y.pack(side="right", fill="y")
        
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal")
        scrollbar_x.pack(side="bottom", fill="x")
        
        # Treeview
        self.tickets_tree = ttk.Treeview(tree_frame, 
                                        yscrollcommand=scrollbar_y.set,
                                        xscrollcommand=scrollbar_x.set,
                                        columns=("ID", "Symbol", "Type", "Lot", "Entry", "SL", "TP", "Strategy"),
                                        show="headings", height=8)
        
        # Configure columns
        self.tickets_tree.heading("ID", text="Ticket ID")
        self.tickets_tree.heading("Symbol", text="Symbol")
        self.tickets_tree.heading("Type", text="Type")
        self.tickets_tree.heading("Lot", text="Lot")
        self.tickets_tree.heading("Entry", text="Entry")
        self.tickets_tree.heading("SL", text="SL")
        self.tickets_tree.heading("TP", text="TP")
        self.tickets_tree.heading("Strategy", text="Strategy")
        
        self.tickets_tree.column("ID", width=100, anchor="center")
        self.tickets_tree.column("Symbol", width=70, anchor="center")
        self.tickets_tree.column("Type", width=50, anchor="center")
        self.tickets_tree.column("Lot", width=50, anchor="center")
        self.tickets_tree.column("Entry", width=70, anchor="center")
        self.tickets_tree.column("SL", width=70, anchor="center")
        self.tickets_tree.column("TP", width=70, anchor="center")
        self.tickets_tree.column("Strategy", width=120, anchor="w")
        
        self.tickets_tree.pack(side="left", fill="both", expand=True)
        
        scrollbar_y.config(command=self.tickets_tree.yview)
        scrollbar_x.config(command=self.tickets_tree.xview)
    
    def sync_chart_symbol(self):
        """ซิงค์สัญลักษณ์จาก Bot ไปหากราฟ"""
        self.chart_symbol_var.set(self.bot_symbol_var.get())
        self.update_chart_now()
    
    def _update_quick_stats(self):
        """อัปเดตสถิติด่วน"""
        if not self.risk_manager:
            stats_text = """
ไม่มีข้อมูล
กรุณาเชื่อมต่อ MT5
"""
        else:
            report = self.risk_manager.get_daily_report()
            stats_text = f"""
📊 สถิติวันนี้
{'━' * 25}
จำนวนไม้: {report['total_trades']}
Win Rate: {report['win_rate']:.1f}%
กำไรสุทธิ: ${report['net_profit']:.2f}

Kill Switch: {'🔴 ON' if self.risk_manager.kill_switch_active else '🟢 OFF'}
"""
        
        self.quick_stats_text.delete(1.0, tk.END)
        self.quick_stats_text.insert(1.0, stats_text)
        
        # Schedule next update
        if self.mt5_handler.is_connected:
            self.root.after(10000, self._update_quick_stats)
    
    def _create_tickets_tab(self):
        """สร้างแท็บสำหรับยืนยันคำสั่งซื้อขาย (MANUAL_CONFIRM mode) - เก็บไว้เพื่อ backward compatibility"""
        pass
    
    def _create_chart_tab(self):
        """สร้างแท็บแสดงกราฟ Real-time - เก็บไว้เพื่อ backward compatibility"""
        pass
    
    def _create_stats_tab(self):
        """สร้างแท็บสถิติและความเสี่ยง"""
        stats_frame = ttk.LabelFrame(self.tab_stats, text="สถิติการเทรด", padding=10)
        stats_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=30, wrap=tk.WORD)
        self.stats_text.pack(fill="both", expand=True)
        
        # ปุ่ม
        btn_frame = ttk.Frame(self.tab_stats)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(btn_frame, text="รายงานวันนี้", command=self.show_daily_report).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="รายงานสัปดาห์นี้", command=self.show_weekly_report).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Reset Kill Switch", 
                  command=self.reset_kill_switch, state="normal").pack(side="left", padx=5)
    
    def _create_connection_frame(self, parent):
        """สร้างส่วนการเชื่อมต่อ"""
        connection_frame = ttk.LabelFrame(parent, text="การเชื่อมต่อ MT5", padding=10)
        connection_frame.pack(fill="x", padx=10, pady=5)
        
        self.status_label = ttk.Label(connection_frame, text="สถานะ: ยังไม่เชื่อมต่อ", foreground="red")
        self.status_label.pack(side="left", padx=5)
        
        self.connect_btn = ttk.Button(connection_frame, text="เชื่อมต่อ MT5", command=self.connect_mt5)
        self.connect_btn.pack(side="left", padx=5)
        
        self.disconnect_btn = ttk.Button(connection_frame, text="ตัดการเชื่อมต่อ", 
                                        command=self.disconnect_mt5, state="disabled")
        self.disconnect_btn.pack(side="left", padx=5)
    
    def _create_account_frame(self, parent):
        """สร้างส่วนแสดงข้อมูลบัญชี"""
        account_frame = ttk.LabelFrame(parent, text="ข้อมูลบัญชี", padding=10)
        account_frame.pack(fill="x", padx=10, pady=5)
        
        # Control bar
        control_bar = ttk.Frame(account_frame)
        control_bar.pack(fill="x", pady=(0, 5))
        
        ttk.Checkbutton(control_bar, text="🔴 Real-time Update",
                       variable=self.account_auto_refresh,
                       command=self.toggle_account_refresh).pack(side="left", padx=5)
        
        self.account_status_label = ttk.Label(control_bar, text="", foreground="green")
        self.account_status_label.pack(side="left", padx=10)
        
        self.account_text = scrolledtext.ScrolledText(account_frame, height=8, wrap=tk.WORD)
        self.account_text.pack(fill="both", expand=True)
    
    def _create_symbol_frame(self, parent):
        """สร้างส่วนเลือกสัญลักษณ์"""
        symbol_frame = ttk.LabelFrame(parent, text="เลือกสัญลักษณ์", padding=10)
        symbol_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(symbol_frame, text="สัญลักษณ์:").pack(side="left", padx=5)
        
        self.symbol_var = tk.StringVar(value="EURUSD")
        self.symbol_entry = ttk.Entry(symbol_frame, textvariable=self.symbol_var, width=15)
        self.symbol_entry.pack(side="left", padx=5)
        
        self.get_price_btn = ttk.Button(symbol_frame, text="ดึงข้อมูลราคา", 
                                       command=self.get_symbol_info, state="disabled")
        self.get_price_btn.pack(side="left", padx=5)
        
        self.get_positions_btn = ttk.Button(symbol_frame, text="ดึงข้อมูลออเดอร์", 
                                           command=self.get_positions, state="disabled")
        self.get_positions_btn.pack(side="left", padx=5)

        ttk.Label(symbol_frame, text="| Real-time:").pack(side="left", padx=10)
        self.auto_refresh_check = ttk.Checkbutton(
            symbol_frame,
            text="เปิด",
            variable=self.auto_refresh_var,
            command=self.toggle_auto_refresh,
            state="disabled"
        )
        self.auto_refresh_check.pack(side="left", padx=5)

        ttk.Label(symbol_frame, text="ทุก (วินาที):").pack(side="left", padx=5)
        self.refresh_interval_entry = ttk.Entry(
            symbol_frame,
            textvariable=self.refresh_interval_var,
            width=5,
            state="disabled"
        )
        self.refresh_interval_entry.pack(side="left", padx=5)
    
    def _create_data_frame(self, parent):
        """สร้างส่วนแสดงข้อมูล"""
        data_frame = ttk.LabelFrame(parent, text="ข้อมูล MT5", padding=10)
        data_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.data_text = scrolledtext.ScrolledText(data_frame, height=20, wrap=tk.WORD)
        self.data_text.pack(fill="both", expand=True)
    
    def connect_mt5(self):
        """เชื่อมต่อกับ MetaTrader5"""
        success, message = self.mt5_handler.connect()
        
        if success:
            self.status_label.config(text="สถานะ: เชื่อมต่อแล้ว", foreground="green")
            self.connect_btn.config(state="disabled")
            self.disconnect_btn.config(state="normal")
            self.get_price_btn.config(state="normal")
            self.get_positions_btn.config(state="normal")
            self.auto_refresh_check.config(state="normal")
            self.refresh_interval_entry.config(state="normal")
            
            # เปิดใช้งาน Bot controls
            self.start_bot_btn.config(state="normal")
            self.scan_btn.config(state="normal")
            
            # สร้าง Execution Engine
            self.exec_engine = ExecutionEngine(self.mt5_handler, self.risk_manager)
            self.exec_engine.set_notification_callback(self.log_bot_message)
            
            self.display_account_info()
            
            # เริ่ม Real-time account update
            if self.account_auto_refresh.get():
                self.start_account_refresh()
            
            messagebox.showinfo("สำเร็จ", message)

            if self.auto_refresh_var.get():
                self.start_auto_refresh()
        else:
            messagebox.showerror("ข้อผิดพลาด", message)
    
    def disconnect_mt5(self):
        """ตัดการเชื่อมต่อจาก MT5"""
        # หยุด Bot ก่อน
        if self.bot_running.get():
            self.stop_bot()
        
        # หยุด Chart refresh
        self.stop_chart_refresh()
        
        # หยุด Account refresh
        self.stop_account_refresh()
        
        success, message = self.mt5_handler.disconnect()
        
        if success:
            self.stop_auto_refresh()
            self.status_label.config(text="สถานะ: ยังไม่เชื่อมต่อ", foreground="red")
            self.connect_btn.config(state="normal")
            self.disconnect_btn.config(state="disabled")
            self.get_price_btn.config(state="disabled")
            self.get_positions_btn.config(state="disabled")
            self.auto_refresh_check.config(state="disabled")
            self.refresh_interval_entry.config(state="disabled")
            
            self.account_text.delete(1.0, tk.END)
            self.data_text.delete(1.0, tk.END)
            
            messagebox.showinfo("สำเร็จ", message)
        else:
            messagebox.showerror("ข้อผิดพลาด", message)
    
    def display_account_info(self):
        """แสดงข้อมูลบัญชีพร้อมสีตามกำไร/ขาดทุน"""
        account_info = self.mt5_handler.get_account_info()
        
        if account_info is None:
            self.account_text.delete(1.0, tk.END)
            self.account_text.insert(tk.END, "ไม่สามารถดึงข้อมูลบัญชีได้\n")
            return
        
        # กำหนดสีตามกำไร/ขาดทุน
        profit = account_info['profit']
        profit_color = "🟢" if profit >= 0 else "🔴"
        profit_text = f"+{profit:.2f}" if profit >= 0 else f"{profit:.2f}"
        
        # คำนวณ % change
        balance = account_info['balance']
        equity = account_info['equity']
        profit_percent = (profit / balance * 100) if balance > 0 else 0
        
        account_data = f"""
ข้อมูลบัญชี MT5 (Real-time)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
หมายเลขบัญชี: {account_info['login']}
ชื่อบริษัท: {account_info['company']}
เซิร์ฟเวอร์: {account_info['server']}
สกุลเงิน: {account_info['currency']}

💰 ยอดเงิน (Balance): {balance:,.2f}
{profit_color} กำไร/ขาดทุน: {profit_text} ({profit_percent:+.2f}%)
💎 Equity: {equity:,.2f}

📊 Margin: {account_info['margin']:,.2f}
🆓 Free Margin: {account_info['margin_free']:,.2f}
📈 Margin Level: {account_info['margin_level']:.2f}%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        self.account_text.delete(1.0, tk.END)
        self.account_text.insert(tk.END, account_data)
        
        # อัปเดตสถานะ
        from datetime import datetime
        time_str = datetime.now().strftime("%H:%M:%S")
        self.account_status_label.config(text=f"อัปเดต: {time_str}")
    
    def toggle_account_refresh(self):
        """เปิด/ปิดการอัปเดตข้อมูลบัญชีอัตโนมัติ"""
        if self.account_auto_refresh.get():
            self.start_account_refresh()
        else:
            self.stop_account_refresh()
    
    def start_account_refresh(self):
        """เริ่มอัปเดตข้อมูลบัญชีอัตโนมัติ"""
        if not self.mt5_handler.is_connected:
            return
        
        self.stop_account_refresh()
        self._account_refresh_loop()
    
    def stop_account_refresh(self):
        """หยุดอัปเดตข้อมูลบัญชีอัตโนมัติ"""
        if self.account_refresh_job:
            try:
                self.root.after_cancel(self.account_refresh_job)
            except:
                pass
            self.account_refresh_job = None
    
    def _account_refresh_loop(self):
        """วนลูปอัปเดตข้อมูลบัญชี"""
        if not self.account_auto_refresh.get() or not self.mt5_handler.is_connected:
            return
        
        try:
            self.display_account_info()
        except Exception as e:
            print(f"Account refresh error: {e}")
        
        # อัปเดตทุก 2 วินาที
        self.account_refresh_job = self.root.after(2000, self._account_refresh_loop)
    
    def get_symbol_info(self):
        """ดึงข้อมูลราคาของสัญลักษณ์"""
        symbol = self.symbol_var.get()
        symbol_info = self.mt5_handler.get_symbol_info(symbol)
        
        if symbol_info is None:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถดึงข้อมูลของ {symbol}")
            return
        
        data = f"""
ข้อมูลราคา: {symbol_info['symbol']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
เวลา: {symbol_info['time']}
Bid: {symbol_info['bid']}
Ask: {symbol_info['ask']}
Last: {symbol_info['last']}
Volume: {symbol_info['volume']}
Spread: {symbol_info['spread']} points
Digits: {symbol_info['digits']}
Point: {symbol_info['point']}
Trade Mode: {symbol_info['trade_mode']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ข้อมูลเพิ่มเติม:
Contract Size: {symbol_info['contract_size']}
Min Volume: {symbol_info['volume_min']}
Max Volume: {symbol_info['volume_max']}
Volume Step: {symbol_info['volume_step']}
"""
        self.data_text.delete(1.0, tk.END)
        self.data_text.insert(tk.END, data)

        self.last_view = "symbol"
    
    def get_positions(self):
        """ดึงข้อมูลออเดอร์ที่เปิดอยู่"""
        positions = self.mt5_handler.get_positions()
        
        if positions is None:
            messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถดึงข้อมูลออเดอร์ได้")
            return
        
        if len(positions) == 0:
            self.data_text.delete(1.0, tk.END)
            self.data_text.insert(tk.END, "ไม่มีออเดอร์ที่เปิดอยู่\n")
            return
        
        data = f"ออเดอร์ที่เปิดอยู่ทั้งหมด ({len(positions)} ออเดอร์):\n"
        data += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, pos in enumerate(positions, 1):
            data += f"ออเดอร์ #{i}:\n"
            data += f"  Ticket: {pos['ticket']}\n"
            data += f"  Symbol: {pos['symbol']}\n"
            data += f"  Type: {pos['type']}\n"
            data += f"  Volume: {pos['volume']}\n"
            data += f"  Open Price: {pos['price_open']}\n"
            data += f"  Current Price: {pos['price_current']}\n"
            data += f"  Stop Loss: {pos['sl']}\n"
            data += f"  Take Profit: {pos['tp']}\n"
            data += f"  Profit: {pos['profit']:.2f}\n"
            data += f"  Open Time: {pos['time']}\n"
            data += f"  Comment: {pos['comment']}\n"
            data += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        self.data_text.delete(1.0, tk.END)
        self.data_text.insert(tk.END, data)

        self.last_view = "positions"

    def toggle_auto_refresh(self):
        """เปิด/ปิดการอัปเดตแบบ Real-time"""
        if self.auto_refresh_var.get():
            self.start_auto_refresh()
        else:
            self.stop_auto_refresh()

    def start_auto_refresh(self):
        """เริ่มการอัปเดตข้อมูลอัตโนมัติ"""
        if not self.mt5_handler.is_connected:
            return
        self.stop_auto_refresh()
        self._refresh_loop()

    def stop_auto_refresh(self):
        """หยุดการอัปเดตข้อมูลอัตโนมัติ"""
        if self.refresh_job is not None:
            try:
                self.root.after_cancel(self.refresh_job)
            except Exception:
                pass
            self.refresh_job = None

    def _refresh_loop(self):
        """วนลูปอัปเดตข้อมูลแบบ Real-time"""
        if not self.mt5_handler.is_connected:
            return

        self.display_account_info()

        if self.last_view == "symbol":
            self.get_symbol_info()
        elif self.last_view == "positions":
            self.get_positions()

        interval_ms = self._get_interval_ms()
        self.refresh_job = self.root.after(interval_ms, self._refresh_loop)

    def _get_interval_ms(self) -> int:
        """ดึงค่าช่วงเวลาเป็นมิลลิวินาที พร้อมป้องกันค่าที่ไม่ถูกต้อง"""
        try:
            seconds = int(self.refresh_interval_var.get())
            if seconds < 1:
                seconds = 1
        except Exception:
            seconds = 2
        return seconds * 1000
    
    # ===== ฟังก์ชันสำหรับ Trading Bot =====
    
    def start_bot(self):
        """เริ่มการทำงานของ Bot"""
        if not self.mt5_handler.is_connected:
            messagebox.showerror("ข้อผิดพลาด", "กรุณาเชื่อมต่อ MT5 ก่อน")
            return
        
        # ตั้งค่าโหมด
        mode_value = self.selected_mode.get()
        for mode in ExecutionMode:
            if mode.value == mode_value:
                set_execution_mode(mode)
                break
        
        self.bot_running.set(True)
        self.start_bot_btn.config(state="disabled")
        self.stop_bot_btn.config(state="normal")
        self.bot_status_label.config(text="สถานะ: 🟢 กำลังทำงาน", foreground="green")
        
        self.log_bot_message(f"🤖 เริ่มการทำงาน | โหมด: {mode_value} | กลยุทธ์: {self.selected_strategy.get()}", "info")
        
        # ซิงค์และอัปเดตกราฟ
        self.sync_chart_symbol()
        
        # เริ่มลูปสแกน
        self._bot_scan_loop()
    
    def stop_bot(self):
        """หยุดการทำงานของ Bot"""
        self.bot_running.set(False)
        self.start_bot_btn.config(state="normal")
        self.stop_bot_btn.config(state="disabled")
        self.bot_status_label.config(text="สถานะ: 🔴 หยุดทำงาน", foreground="red")
        
        self.log_bot_message("⏹ หยุดการทำงาน", "warning")
    
    def _bot_scan_loop(self):
        """วนลูปสแกนสัญญาณ"""
        if not self.bot_running.get():
            return
        
        try:
            self._scan_and_process()
        except Exception as e:
            self.log_bot_message(f"❌ เกิดข้อผิดพลาด: {str(e)}", "error")
        
        # วนลูปทุก 60 วินาที (สำหรับ D1)
        self.root.after(60000, self._bot_scan_loop)
    
    def manual_scan(self):
        """สแกนด้วยตนเองทันที"""
        if not self.mt5_handler.is_connected:
            messagebox.showerror("ข้อผิดพลาด", "กรุณาเชื่อมต่อ MT5 ก่อน")
            return
        
        self.log_bot_message("🔍 เริ่มสแกนสัญญาณ...", "info")
        self._scan_and_process()
    
    def _scan_and_process(self):
        """สแกนและประมวลผลสัญญาณ"""
        symbol = self.bot_symbol_var.get()
        
        # ดึงข้อมูลแท่งเทียน
        data = self.mt5_handler.get_historical_data(symbol, "D1", 100)
        if not data:
            self.log_bot_message(f"❌ ไม่สามารถดึงข้อมูล {symbol}", "error")
            return
        
        high = np.array(data['high'])
        low = np.array(data['low'])
        close = np.array(data['close'])
        
        # เลือกกลยุทธ์
        strategy_value = self.selected_strategy.get()
        strategy_type = None
        for strat in StrategyType:
            if strat.value == strategy_value:
                strategy_type = strat
                break
        
        if not strategy_type:
            self.log_bot_message("❌ ไม่พบกลยุทธ์ที่เลือก", "error")
            return
        
        # สร้างสัญญาณ
        signal = self.signal_engine.generate_signal(symbol, strategy_type, high, low, close)
        
        self.log_bot_message(f"📊 สัญญาณ: {signal.signal.value if hasattr(signal.signal, 'value') else str(signal.signal)} | {signal.reason}", "info")
        
        # ส่งไปยัง Execution Engine
        if self.exec_engine:
            result = self.exec_engine.process_signal(signal)
            
            # รีเฟรชตั๋วถ้าอยู่ในโหมด MANUAL_CONFIRM
            if get_execution_mode() == ExecutionMode.MANUAL_CONFIRM:
                self.refresh_tickets()
            
            # อัปเดต Quick Stats
            self._update_quick_stats()
    
    def log_bot_message(self, message: str, level: str = "info"):
        """บันทึก log ใน GUI"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        color = "black"
        if level == "error":
            color = "red"
        elif level == "warning":
            color = "orange"
        elif level == "success":
            color = "green"
        
        self.bot_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.bot_log.see(tk.END)
    
    def approve_ticket(self):
        """อนุมัติตั๋วคำสั่ง"""
        selected = self.tickets_tree.selection()
        if not selected:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกตั๋วที่ต้องการอนุมัติ")
            return
        
        ticket_id = self.tickets_tree.item(selected[0])['values'][0]
        
        if self.exec_engine:
            result = self.exec_engine.approve_ticket(ticket_id)
            if result['success']:
                messagebox.showinfo("สำเร็จ", result['message'])
                self.log_bot_message(f"✅ อนุมัติตั๋ว {ticket_id}", "success")
                self.refresh_tickets()
            else:
                messagebox.showerror("ข้อผิดพลาด", result['message'])
    
    def reject_ticket(self):
        """ปฏิเสธตั๋วคำสั่ง"""
        selected = self.tickets_tree.selection()
        if not selected:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกตั๋วที่ต้องการปฏิเสธ")
            return
        
        ticket_id = self.tickets_tree.item(selected[0])['values'][0]
        
        if self.exec_engine:
            result = self.exec_engine.reject_ticket(ticket_id)
            if result['success']:
                messagebox.showinfo("สำเร็จ", result['message'])
                self.log_bot_message(f"🚫 ปฏิเสธตั๋ว {ticket_id}", "warning")
                self.refresh_tickets()
            else:
                messagebox.showerror("ข้อผิดพลาด", result['message'])
    
    def refresh_tickets(self):
        """รีเฟรชรายการตั๋ว"""
        # ลบข้อมูลเก่า
        for item in self.tickets_tree.get_children():
            self.tickets_tree.delete(item)
        
        if not self.exec_engine:
            return
        
        # เพิ่มตั๋วที่รอยืนยัน
        pending_tickets = self.exec_engine.get_pending_tickets()
        for ticket in pending_tickets:
            signal_value = ticket.signal.signal.value if hasattr(ticket.signal.signal, 'value') else str(ticket.signal.signal)
            
            self.tickets_tree.insert("", "end", values=(
                ticket.id,
                ticket.signal.symbol,
                signal_value,
                f"{ticket.lot_size:.2f}",
                f"{ticket.signal.entry_price:.5f}",
                f"{ticket.signal.stop_loss:.5f}",
                f"{ticket.signal.take_profit:.5f}",
                ticket.signal.strategy.value
            ))
    
    def show_daily_report(self):
        """แสดงรายงานประจำวัน"""
        if not self.risk_manager:
            return
        
        report = self.risk_manager.get_daily_report()
        
        text = f"""
═══════════════════════════════════════
รายงานการเทรดประจำวัน
วันที่: {report['date']}
═══════════════════════════════════════

จำนวนไม้รวม: {report['total_trades']}
ชนะ: {report['winning_trades']} ไม้
แพ้: {report['losing_trades']} ไม้
Win Rate: {report['win_rate']:.2f}%

กำไรรวม: ${report['total_profit']:.2f}
ขาดทุนรวม: ${report['total_loss']:.2f}
กำไรสุทธิ: ${report['net_profit']:.2f}

═══════════════════════════════════════
จำนวนไม้ต่อสัญลักษณ์:
"""
        
        for symbol, count in report['symbols_traded'].items():
            text += f"  {symbol}: {count} ไม้\n"
        
        text += "═══════════════════════════════════════\n"
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, text)
    
    def show_weekly_report(self):
        """แสดงรายงานประจำสัปดาห์"""
        if not self.risk_manager:
            return
        
        report = self.risk_manager.get_weekly_report()
        
        text = f"""
═══════════════════════════════════════
รายงานการเทรดประจำสัปดาห์
สัปดาห์: {report['week']}
═══════════════════════════════════════

จำนวนไม้รวม: {report['total_trades']}
ชนะ: {report['winning_trades']} ไม้
แพ้: {report['losing_trades']} ไม้
Win Rate: {report['win_rate']:.2f}%

กำไรรวม: ${report['total_profit']:.2f}
ขาดทุนรวม: ${report['total_loss']:.2f}
กำไรสุทธิ: ${report['net_profit']:.2f}

═══════════════════════════════════════
จำนวนไม้ต่อสัญลักษณ์:
"""
        
        for symbol, count in report['symbols_traded'].items():
            text += f"  {symbol}: {count} ไม้\n"
        
        text += "═══════════════════════════════════════\n"
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, text)
    
    def reset_kill_switch(self):
        """รีเซ็ต Kill Switch"""
        if not self.risk_manager:
            return
        
        if messagebox.askyesno("ยืนยัน", "คุณแน่ใจว่าต้องการรีเซ็ต Kill Switch?"):
            self.risk_manager.deactivate_kill_switch()
            self.log_bot_message("✅ รีเซ็ต Kill Switch สำเร็จ", "success")
            messagebox.showinfo("สำเร็จ", "รีเซ็ต Kill Switch แล้ว")
    
    # ===== ฟังก์ชันสำหรับ Chart =====
    
    def update_chart_now(self):
        """อัปเดตกราฟทันที"""
        if not self.mt5_handler.is_connected:
            messagebox.showerror("ข้อผิดพลาด", "กรุณาเชื่อมต่อ MT5 ก่อน")
            return
        
        self.chart_status_label.config(text="กำลังโหลด...", foreground="orange")
        self.root.update()
        
        try:
            symbol = self.chart_symbol_var.get()
            strategy_value = self.chart_strategy_var.get()
            
            # หากลยุทธ์
            strategy_type = None
            for strat in StrategyType:
                if strat.value == strategy_value:
                    strategy_type = strat
                    break
            
            if not strategy_type:
                self.chart_status_label.config(text="ไม่พบกลยุทธ์", foreground="red")
                return
            
            # ดึงข้อมูล
            data = self.mt5_handler.get_historical_data(symbol, "D1", 100)
            if not data:
                self.chart_status_label.config(text=f"ไม่สามารถดึงข้อมูล {symbol}", foreground="red")
                return
            
            # สร้างสัญญาณ
            high = np.array(data['high'])
            low = np.array(data['low'])
            close = np.array(data['close'])
            
            signal = self.signal_engine.generate_signal(symbol, strategy_type, high, low, close)
            
            # สร้าง/อัปเดต Chart Visualizer
            if self.chart_visualizer is None:
                # ล้างพื้นที่เก่า
                for widget in self.chart_container.winfo_children():
                    widget.destroy()
                
                self.chart_visualizer = ChartVisualizer(self.chart_container, strategy_type)
            elif self.chart_visualizer.strategy_type != strategy_type:
                # เปลี่ยนกลยุทธ์ = สร้างใหม่
                for widget in self.chart_container.winfo_children():
                    widget.destroy()
                
                self.chart_visualizer = ChartVisualizer(self.chart_container, strategy_type)
            
            # อัปเดตกราฟ
            self.chart_visualizer.update_chart(data, signal)
            
            # แสดงสถานะ
            signal_text = signal.signal.value if hasattr(signal.signal, 'value') else str(signal.signal)
            self.chart_status_label.config(
                text=f"อัปเดต: {symbol} | สัญญาณ: {signal_text}", 
                foreground="green"
            )
            
        except Exception as e:
            self.chart_status_label.config(text=f"Error: {str(e)}", foreground="red")
            print(f"Chart Error: {e}")
    
    def toggle_chart_refresh(self):
        """เปิด/ปิดการอัปเดตกราฟอัตโนมัติ"""
        if self.chart_auto_refresh.get():
            self.start_chart_refresh()
        else:
            self.stop_chart_refresh()
    
    def start_chart_refresh(self):
        """เริ่มอัปเดตกราฟอัตโนมัติ"""
        if not self.mt5_handler.is_connected:
            return
        
        self.stop_chart_refresh()
        self._chart_refresh_loop()
    
    def stop_chart_refresh(self):
        """หยุดอัปเดตกราฟอัตโนมัติ"""
        if self.chart_refresh_job:
            try:
                self.root.after_cancel(self.chart_refresh_job)
            except:
                pass
            self.chart_refresh_job = None
    
    def _chart_refresh_loop(self):
        """วนลูปอัปเดตกราฟ"""
        if not self.chart_auto_refresh.get() or not self.mt5_handler.is_connected:
            return
        
        self.update_chart_now()
        
        # อัปเดตทุก 5 วินาที
        self.chart_refresh_job = self.root.after(5000, self._chart_refresh_loop)
