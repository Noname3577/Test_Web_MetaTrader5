"""
Chart Visualizer - แสดงกราฟแท่งเทียนพร้อม Indicators แบบ Real-time
"""

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional, List

from strategies import TechnicalIndicators
from config import StrategyType, get_strategy_config


class ChartVisualizer:
    """คลาสสำหรับสร้างและอัปเดตกราฟแบบ Real-time"""
    
    def __init__(self, parent_frame, strategy_type: StrategyType):
        self.parent = parent_frame
        self.strategy_type = strategy_type
        self.config = get_strategy_config(strategy_type)
        
        # สร้าง Figure
        self.fig = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # สร้าง subplots
        self.ax_main = self.fig.add_subplot(3, 1, 1)  # กราฟแท่งเทียน + indicators
        self.ax_volume = self.fig.add_subplot(3, 1, 2, sharex=self.ax_main)  # Volume
        self.ax_indicator = self.fig.add_subplot(3, 1, 3, sharex=self.ax_main)  # Indicator ล่าง
        
        self.fig.tight_layout()
        
        # ข้อมูลสัญญาณล่าสุด
        self.last_signal = None
    
    def update_chart(self, data: Dict, signal=None):
        """
        อัปเดตกราฟด้วยข้อมูลใหม่
        
        Args:
            data: {'time': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}
            signal: TradingSignal object (optional)
        """
        if not data or len(data.get('close', [])) == 0:
            return
        
        self.last_signal = signal
        
        # แปลงเป็น numpy arrays
        times = data['time']
        opens = np.array(data['open'])
        highs = np.array(data['high'])
        lows = np.array(data['low'])
        closes = np.array(data['close'])
        volumes = np.array(data['volume'])
        
        # ล้างกราฟเก่า
        self.ax_main.clear()
        self.ax_volume.clear()
        self.ax_indicator.clear()
        
        # วาดกราฟตามกลยุทธ์
        if self.strategy_type == StrategyType.MA_CROSSOVER:
            self._draw_ma_crossover(times, opens, highs, lows, closes, volumes)
        elif self.strategy_type == StrategyType.BOLLINGER_BANDS:
            self._draw_bollinger_bands(times, opens, highs, lows, closes, volumes)
        elif self.strategy_type == StrategyType.RSI_SWING:
            self._draw_rsi_swing(times, opens, highs, lows, closes, volumes)
        elif self.strategy_type == StrategyType.MACD:
            self._draw_macd(times, opens, highs, lows, closes, volumes)
        elif self.strategy_type == StrategyType.SUPERTREND:
            self._draw_supertrend(times, opens, highs, lows, closes, volumes)
        elif self.strategy_type == StrategyType.DONCHIAN_BREAKOUT:
            self._draw_donchian(times, opens, highs, lows, closes, volumes)
        else:
            self._draw_basic_chart(times, opens, highs, lows, closes, volumes)
        
        # วาด Signal Markers
        if signal and signal.signal.value != "NO_TRADE":
            self._draw_signal_marker(times, closes, signal)
        
        # Format และอัปเดต
        self.ax_main.grid(True, alpha=0.3)
        self.ax_volume.grid(True, alpha=0.3)
        self.ax_indicator.grid(True, alpha=0.3)
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def _draw_candlesticks(self, times, opens, highs, lows, closes, ax):
        """วาดแท่งเทียน"""
        width = 0.6
        
        for i in range(len(closes)):
            color = 'green' if closes[i] >= opens[i] else 'red'
            
            # เส้นแนวตั้ง (high-low)
            ax.plot([i, i], [lows[i], highs[i]], color=color, linewidth=1)
            
            # กล่องแท่งเทียน
            height = abs(closes[i] - opens[i])
            bottom = min(opens[i], closes[i])
            ax.add_patch(plt.Rectangle((i - width/2, bottom), width, height, 
                                       facecolor=color, edgecolor=color, alpha=0.8))
        
        ax.set_xlim(-1, len(closes))
        
        # Format x-axis
        step = max(1, len(times) // 10)
        x_ticks = range(0, len(times), step)
        x_labels = [times[i].strftime('%m/%d') for i in x_ticks]
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(x_labels, rotation=45)
    
    def _draw_ma_crossover(self, times, opens, highs, lows, closes, volumes):
        """วาดกราฟ MA Crossover"""
        # วาดแท่งเทียน
        self._draw_candlesticks(times, opens, highs, lows, closes, self.ax_main)
        
        # คำนวณ MA
        fast_period = self.config.get('fast_period', 10)
        slow_period = self.config.get('slow_period', 30)
        
        ema_fast = TechnicalIndicators.ema(closes, fast_period)
        ema_slow = TechnicalIndicators.ema(closes, slow_period)
        
        # วาด MA
        x = range(len(closes))
        self.ax_main.plot(x, ema_fast, label=f'EMA {fast_period}', color='blue', linewidth=2)
        self.ax_main.plot(x, ema_slow, label=f'EMA {slow_period}', color='orange', linewidth=2)
        
        self.ax_main.set_title(f'MA Crossover Strategy', fontsize=12, fontweight='bold')
        self.ax_main.set_ylabel('Price')
        self.ax_main.legend(loc='upper left')
        
        # Volume
        self._draw_volume(volumes)
        
        # ATR
        atr = TechnicalIndicators.atr(highs, lows, closes, 14)
        self.ax_indicator.plot(range(len(atr)), atr, label='ATR(14)', color='purple', linewidth=2)
        self.ax_indicator.set_ylabel('ATR')
        self.ax_indicator.legend(loc='upper left')
    
    def _draw_bollinger_bands(self, times, opens, highs, lows, closes, volumes):
        """วาดกราฟ Bollinger Bands"""
        self._draw_candlesticks(times, opens, highs, lows, closes, self.ax_main)
        
        # คำนวณ Bollinger Bands
        period = self.config.get('period', 20)
        std_dev = self.config.get('std_dev', 2.0)
        
        upper, middle, lower = TechnicalIndicators.bollinger_bands(closes, period, std_dev)
        
        x = range(len(closes))
        self.ax_main.plot(x, upper, label='Upper BB', color='red', linestyle='--', linewidth=1.5)
        self.ax_main.plot(x, middle, label='Middle BB', color='blue', linewidth=2)
        self.ax_main.plot(x, lower, label='Lower BB', color='green', linestyle='--', linewidth=1.5)
        self.ax_main.fill_between(x, upper, lower, alpha=0.1, color='gray')
        
        self.ax_main.set_title('Bollinger Bands Strategy', fontsize=12, fontweight='bold')
        self.ax_main.set_ylabel('Price')
        self.ax_main.legend(loc='upper left')
        
        # Volume
        self._draw_volume(volumes)
        
        # RSI
        rsi = TechnicalIndicators.rsi(closes, self.config.get('rsi_period', 14))
        self.ax_indicator.plot(range(len(rsi)), rsi, label='RSI(14)', color='purple', linewidth=2)
        self.ax_indicator.axhline(y=70, color='r', linestyle='--', alpha=0.5)
        self.ax_indicator.axhline(y=30, color='g', linestyle='--', alpha=0.5)
        self.ax_indicator.set_ylabel('RSI')
        self.ax_indicator.set_ylim(0, 100)
        self.ax_indicator.legend(loc='upper left')
    
    def _draw_rsi_swing(self, times, opens, highs, lows, closes, volumes):
        """วาดกราฟ RSI Swing"""
        self._draw_candlesticks(times, opens, highs, lows, closes, self.ax_main)
        
        self.ax_main.set_title('RSI Swing Strategy', fontsize=12, fontweight='bold')
        self.ax_main.set_ylabel('Price')
        
        # Volume
        self._draw_volume(volumes)
        
        # RSI
        rsi_period = self.config.get('rsi_period', 14)
        rsi = TechnicalIndicators.rsi(closes, rsi_period)
        
        x = range(len(rsi))
        self.ax_indicator.plot(x, rsi, label=f'RSI({rsi_period})', color='purple', linewidth=2)
        self.ax_indicator.axhline(y=self.config.get('overbought_level', 70), 
                                  color='r', linestyle='--', alpha=0.5, label='Overbought')
        self.ax_indicator.axhline(y=self.config.get('oversold_level', 30), 
                                  color='g', linestyle='--', alpha=0.5, label='Oversold')
        self.ax_indicator.axhline(y=50, color='gray', linestyle=':', alpha=0.3)
        self.ax_indicator.fill_between(x, 70, 100, alpha=0.1, color='red')
        self.ax_indicator.fill_between(x, 0, 30, alpha=0.1, color='green')
        
        self.ax_indicator.set_ylabel('RSI')
        self.ax_indicator.set_ylim(0, 100)
        self.ax_indicator.legend(loc='upper left')
    
    def _draw_macd(self, times, opens, highs, lows, closes, volumes):
        """วาดกราฟ MACD"""
        self._draw_candlesticks(times, opens, highs, lows, closes, self.ax_main)
        
        self.ax_main.set_title('MACD Strategy', fontsize=12, fontweight='bold')
        self.ax_main.set_ylabel('Price')
        
        # Volume
        self._draw_volume(volumes)
        
        # MACD
        fast = self.config.get('fast_period', 12)
        slow = self.config.get('slow_period', 26)
        signal_period = self.config.get('signal_period', 9)
        
        macd_line, signal_line, histogram = TechnicalIndicators.macd(closes, fast, slow, signal_period)
        
        x = range(len(macd_line))
        self.ax_indicator.plot(x, macd_line, label='MACD', color='blue', linewidth=2)
        self.ax_indicator.plot(x, signal_line, label='Signal', color='red', linewidth=2)
        
        # Histogram
        colors = ['green' if h >= 0 else 'red' for h in histogram]
        self.ax_indicator.bar(x, histogram, color=colors, alpha=0.3, label='Histogram')
        self.ax_indicator.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        self.ax_indicator.set_ylabel('MACD')
        self.ax_indicator.legend(loc='upper left')
    
    def _draw_supertrend(self, times, opens, highs, lows, closes, volumes):
        """วาดกราฟ Supertrend"""
        self._draw_candlesticks(times, opens, highs, lows, closes, self.ax_main)
        
        # คำนวณ Supertrend
        atr_period = self.config.get('atr_period', 10)
        multiplier = self.config.get('atr_multiplier', 3.0)
        
        supertrend_line, direction = TechnicalIndicators.supertrend(
            highs, lows, closes, atr_period, multiplier
        )
        
        # วาดเส้น Supertrend
        x = range(len(closes))
        for i in range(1, len(closes)):
            color = 'green' if direction[i] == 1 else 'red'
            self.ax_main.plot([i-1, i], [supertrend_line[i-1], supertrend_line[i]], 
                            color=color, linewidth=2.5, alpha=0.8)
        
        self.ax_main.set_title('Supertrend Strategy', fontsize=12, fontweight='bold')
        self.ax_main.set_ylabel('Price')
        
        # Volume
        self._draw_volume(volumes)
        
        # ATR
        atr = TechnicalIndicators.atr(highs, lows, closes, atr_period)
        self.ax_indicator.plot(range(len(atr)), atr, label=f'ATR({atr_period})', 
                              color='purple', linewidth=2)
        self.ax_indicator.set_ylabel('ATR')
        self.ax_indicator.legend(loc='upper left')
    
    def _draw_donchian(self, times, opens, highs, lows, closes, volumes):
        """วาดกราฟ Donchian Channel"""
        self._draw_candlesticks(times, opens, highs, lows, closes, self.ax_main)
        
        # คำนวณ Donchian Channel
        entry_period = self.config.get('entry_period', 20)
        upper, lower = TechnicalIndicators.donchian_channel(highs, lows, entry_period)
        
        x = range(len(closes))
        self.ax_main.plot(x, upper, label=f'Upper({entry_period})', 
                         color='red', linestyle='--', linewidth=1.5)
        self.ax_main.plot(x, lower, label=f'Lower({entry_period})', 
                         color='green', linestyle='--', linewidth=1.5)
        self.ax_main.fill_between(x, upper, lower, alpha=0.05, color='blue')
        
        self.ax_main.set_title('Donchian Breakout Strategy', fontsize=12, fontweight='bold')
        self.ax_main.set_ylabel('Price')
        self.ax_main.legend(loc='upper left')
        
        # Volume
        self._draw_volume(volumes)
        
        # ATR
        atr = TechnicalIndicators.atr(highs, lows, closes, 14)
        self.ax_indicator.plot(range(len(atr)), atr, label='ATR(14)', 
                              color='purple', linewidth=2)
        self.ax_indicator.set_ylabel('ATR')
        self.ax_indicator.legend(loc='upper left')
    
    def _draw_basic_chart(self, times, opens, highs, lows, closes, volumes):
        """วาดกราฟพื้นฐาน"""
        self._draw_candlesticks(times, opens, highs, lows, closes, self.ax_main)
        self.ax_main.set_title('Price Chart', fontsize=12, fontweight='bold')
        self.ax_main.set_ylabel('Price')
        self._draw_volume(volumes)
    
    def _draw_volume(self, volumes):
        """วาด Volume bar"""
        x = range(len(volumes))
        self.ax_volume.bar(x, volumes, color='gray', alpha=0.5)
        self.ax_volume.set_ylabel('Volume')
    
    def _draw_signal_marker(self, times, closes, signal):
        """วาด marker บนกราฟเมื่อมีสัญญาณ"""
        if not signal or signal.signal.value == "NO_TRADE":
            return
        
        # วาด marker ที่แท่งสุดท้าย
        last_idx = len(closes) - 1
        
        if signal.signal.value == "BUY":
            # ลูกศรขึ้น สีเขียว
            self.ax_main.annotate('▲ BUY', 
                                 xy=(last_idx, closes[last_idx]),
                                 xytext=(last_idx, closes[last_idx] * 0.995),
                                 fontsize=14, fontweight='bold', color='green',
                                 ha='center',
                                 arrowprops=dict(arrowstyle='->', color='green', lw=2))
            
            # วาดเส้น SL/TP
            self.ax_main.axhline(y=signal.stop_loss, color='red', 
                               linestyle='--', linewidth=1, alpha=0.7, label='Stop Loss')
            self.ax_main.axhline(y=signal.take_profit, color='green', 
                               linestyle='--', linewidth=1, alpha=0.7, label='Take Profit')
        
        elif signal.signal.value == "SELL":
            # ลูกศรลง สีแดง
            self.ax_main.annotate('▼ SELL', 
                                 xy=(last_idx, closes[last_idx]),
                                 xytext=(last_idx, closes[last_idx] * 1.005),
                                 fontsize=14, fontweight='bold', color='red',
                                 ha='center',
                                 arrowprops=dict(arrowstyle='->', color='red', lw=2))
            
            # วาดเส้น SL/TP
            self.ax_main.axhline(y=signal.stop_loss, color='red', 
                               linestyle='--', linewidth=1, alpha=0.7, label='Stop Loss')
            self.ax_main.axhline(y=signal.take_profit, color='green', 
                               linestyle='--', linewidth=1, alpha=0.7, label='Take Profit')
        
        self.ax_main.legend(loc='upper left')
    
    def clear_chart(self):
        """ล้างกราฟ"""
        self.ax_main.clear()
        self.ax_volume.clear()
        self.ax_indicator.clear()
        self.canvas.draw()
