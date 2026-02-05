"""
Strategy Library - กลยุทธ์การเทรด 7 แบบ
พร้อมสูตรคำนวณและตัวอย่างการใช้งาน
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from enum import Enum


class SignalType(Enum):
    """ประเภทของสัญญาณ"""
    BUY = "BUY"
    SELL = "SELL"
    NO_TRADE = "NO_TRADE"


class TechnicalIndicators:
    """คลาสสำหรับคำนวณ Technical Indicators"""
    
    @staticmethod
    def sma(data: np.ndarray, period: int) -> np.ndarray:
        """
        Simple Moving Average
        SMA = (P1 + P2 + ... + Pn) / n
        """
        return pd.Series(data).rolling(window=period).mean().values
    
    @staticmethod
    def ema(data: np.ndarray, period: int) -> np.ndarray:
        """
        Exponential Moving Average
        EMA_t = α * P_t + (1-α) * EMA_{t-1}
        α = 2/(n+1)
        """
        return pd.Series(data).ewm(span=period, adjust=False).mean().values
    
    @staticmethod
    def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Average True Range (Wilder's smoothing)
        TR = max(High-Low, |High-Close_prev|, |Low-Close_prev|)
        ATR = Wilder's smoothing of TR
        """
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))
        
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        tr[0] = tr1[0]  # แก้ไขค่าแรก
        
        # Wilder's smoothing
        atr = pd.Series(tr).ewm(alpha=1/period, adjust=False).mean().values
        return atr
    
    @staticmethod
    def rsi(data: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Relative Strength Index
        RSI = 100 - (100 / (1 + RS))
        RS = AvgGain / AvgLoss
        """
        delta = np.diff(data)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        # เติม 0 ตัวแรก
        gain = np.insert(gain, 0, 0)
        loss = np.insert(loss, 0, 0)
        
        avg_gain = pd.Series(gain).ewm(alpha=1/period, adjust=False).mean().values
        avg_loss = pd.Series(loss).ewm(alpha=1/period, adjust=False).mean().values
        
        rs = avg_gain / (avg_loss + 1e-10)  # ป้องกันหารด้วย 0
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def bollinger_bands(data: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Bollinger Bands
        Middle = SMA(n)
        Upper = Middle + k*σ
        Lower = Middle - k*σ
        
        Returns: (upper, middle, lower)
        """
        middle = pd.Series(data).rolling(window=period).mean().values
        std = pd.Series(data).rolling(window=period).std().values
        
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        
        return upper, middle, lower
    
    @staticmethod
    def macd(data: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        MACD (Moving Average Convergence Divergence)
        MACD = EMA(fast) - EMA(slow)
        Signal = EMA(MACD, signal_period)
        Histogram = MACD - Signal
        
        Returns: (macd_line, signal_line, histogram)
        """
        ema_fast = pd.Series(data).ewm(span=fast, adjust=False).mean().values
        ema_slow = pd.Series(data).ewm(span=slow, adjust=False).mean().values
        
        macd_line = ema_fast - ema_slow
        signal_line = pd.Series(macd_line).ewm(span=signal, adjust=False).mean().values
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def donchian_channel(high: np.ndarray, low: np.ndarray, period: int = 20) -> Tuple[np.ndarray, np.ndarray]:
        """
        Donchian Channel
        Upper = Highest High over n periods
        Lower = Lowest Low over n periods
        
        Returns: (upper, lower)
        """
        upper = pd.Series(high).rolling(window=period).max().values
        lower = pd.Series(low).rolling(window=period).min().values
        
        return upper, lower
    
    @staticmethod
    def supertrend(high: np.ndarray, low: np.ndarray, close: np.ndarray, 
                   atr_period: int = 10, multiplier: float = 3.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Supertrend Indicator
        Basic Upper Band = (High + Low)/2 + Multiplier * ATR
        Basic Lower Band = (High + Low)/2 - Multiplier * ATR
        
        Returns: (supertrend_line, trend_direction)
        trend_direction: 1 = uptrend, -1 = downtrend
        """
        atr = TechnicalIndicators.atr(high, low, close, atr_period)
        hl_avg = (high + low) / 2
        
        basic_upper = hl_avg + (multiplier * atr)
        basic_lower = hl_avg - (multiplier * atr)
        
        supertrend = np.zeros_like(close)
        direction = np.ones_like(close)
        
        for i in range(1, len(close)):
            # Upper band
            if close[i-1] > basic_upper[i-1]:
                basic_upper[i] = max(basic_upper[i], basic_upper[i-1])
            
            # Lower band
            if close[i-1] < basic_lower[i-1]:
                basic_lower[i] = min(basic_lower[i], basic_lower[i-1])
            
            # Determine trend
            if close[i] <= basic_upper[i]:
                supertrend[i] = basic_upper[i]
                direction[i] = -1  # Downtrend
            else:
                supertrend[i] = basic_lower[i]
                direction[i] = 1  # Uptrend
        
        return supertrend, direction


class Strategy1_MACrossover:
    """
    กลยุทธ์ 1: Moving Average Crossover
    เข้า Long: EMA fast ตัดขึ้น EMA slow และปิดเหนือทั้งคู่
    ออก Long: EMA fast ตัดลง EMA slow
    """
    
    @staticmethod
    def generate_signal(high: np.ndarray, low: np.ndarray, close: np.ndarray, 
                       fast_period: int = 10, slow_period: int = 30, 
                       atr_period: int = 14, atr_multiplier: float = 2.0) -> Dict:
        """
        สร้างสัญญาณจากกลยุทธ์ MA Crossover
        
        Returns:
            {
                'signal': SignalType,
                'entry_price': float,
                'stop_loss': float,
                'take_profit': float,
                'atr': float,
                'reason': str
            }
        """
        if len(close) < max(fast_period, slow_period, atr_period) + 2:
            return {'signal': SignalType.NO_TRADE, 'reason': 'ข้อมูลไม่เพียงพอ'}
        
        # คำนวณ indicators
        ema_fast = TechnicalIndicators.ema(close, fast_period)
        ema_slow = TechnicalIndicators.ema(close, slow_period)
        atr = TechnicalIndicators.atr(high, low, close, atr_period)
        
        # ใช้เฉพาะแท่งที่ปิดแล้ว (index -2) และแท่งล่าสุด (-1)
        prev_fast = ema_fast[-2]
        prev_slow = ema_slow[-2]
        curr_fast = ema_fast[-1]
        curr_slow = ema_slow[-1]
        curr_close = close[-1]
        curr_atr = atr[-1]
        
        signal = SignalType.NO_TRADE
        reason = ""
        
        # ตรวจสอบ crossover (Long)
        if prev_fast <= prev_slow and curr_fast > curr_slow and curr_close > curr_fast:
            signal = SignalType.BUY
            reason = f"EMA{fast_period} ตัดขึ้น EMA{slow_period}"
            entry_price = curr_close
            stop_loss = entry_price - (atr_multiplier * curr_atr)
            take_profit = entry_price + (atr_multiplier * curr_atr * 2)  # RR 1:2
            
            return {
                'signal': signal,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'atr': curr_atr,
                'reason': reason
            }
        
        # ตรวจสอบ crossover (Short)
        elif prev_fast >= prev_slow and curr_fast < curr_slow and curr_close < curr_fast:
            signal = SignalType.SELL
            reason = f"EMA{fast_period} ตัดลง EMA{slow_period}"
            entry_price = curr_close
            stop_loss = entry_price + (atr_multiplier * curr_atr)
            take_profit = entry_price - (atr_multiplier * curr_atr * 2)
            
            return {
                'signal': signal,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'atr': curr_atr,
                'reason': reason
            }
        
        return {'signal': SignalType.NO_TRADE, 'reason': 'ไม่มีสัญญาณ crossover'}


class Strategy2_DonchianBreakout:
    """
    กลยุทธ์ 2: Donchian Channel Breakout (Turtle Trading)
    เข้า Long: Close ทะลุ HighestHigh(N)
    ออก Long: Close หลุด LowestLow(M)
    """
    
    @staticmethod
    def generate_signal(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                       entry_period: int = 20, exit_period: int = 10,
                       atr_period: int = 14, atr_multiplier: float = 2.0) -> Dict:
        """สร้างสัญญาณจาก Donchian Breakout"""
        
        if len(close) < max(entry_period, exit_period, atr_period) + 2:
            return {'signal': SignalType.NO_TRADE, 'reason': 'ข้อมูลไม่เพียงพอ'}
        
        # คำนวณ Donchian Channel
        upper_entry, lower_entry = TechnicalIndicators.donchian_channel(high, low, entry_period)
        atr = TechnicalIndicators.atr(high, low, close, atr_period)
        
        prev_close = close[-2]
        curr_close = close[-1]
        prev_upper = upper_entry[-3]  # ใช้ค่า N แท่งก่อนหน้า (ไม่นับแท่งปัจจุบัน)
        prev_lower = lower_entry[-3]
        curr_atr = atr[-1]
        
        # Long breakout
        if prev_close <= prev_upper and curr_close > prev_upper:
            return {
                'signal': SignalType.BUY,
                'entry_price': curr_close,
                'stop_loss': curr_close - (atr_multiplier * curr_atr),
                'take_profit': curr_close + (atr_multiplier * curr_atr * 3),  # RR 1:3
                'atr': curr_atr,
                'reason': f'ทะลุ Donchian Upper ({entry_period} periods)'
            }
        
        # Short breakout
        elif prev_close >= prev_lower and curr_close < prev_lower:
            return {
                'signal': SignalType.SELL,
                'entry_price': curr_close,
                'stop_loss': curr_close + (atr_multiplier * curr_atr),
                'take_profit': curr_close - (atr_multiplier * curr_atr * 3),
                'atr': curr_atr,
                'reason': f'หลุด Donchian Lower ({entry_period} periods)'
            }
        
        return {'signal': SignalType.NO_TRADE, 'reason': 'ไม่มี breakout'}


class Strategy3_BollingerBands:
    """
    กลยุทธ์ 3: Bollinger Bands + RSI (Mean Reversion)
    เข้า Long: Close < LowerBand และ RSI < 30
    ออก Long: Close กลับที่ MiddleBand หรือ RSI > 50
    """
    
    @staticmethod
    def generate_signal(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                       bb_period: int = 20, std_dev: float = 2.0,
                       rsi_period: int = 14, rsi_oversold: float = 30,
                       rsi_overbought: float = 70,
                       atr_period: int = 14, atr_multiplier: float = 1.5) -> Dict:
        """สร้างสัญญาณจาก Bollinger Bands + RSI"""
        
        if len(close) < max(bb_period, rsi_period, atr_period) + 2:
            return {'signal': SignalType.NO_TRADE, 'reason': 'ข้อมูลไม่เพียงพอ'}
        
        upper, middle, lower = TechnicalIndicators.bollinger_bands(close, bb_period, std_dev)
        rsi = TechnicalIndicators.rsi(close, rsi_period)
        atr = TechnicalIndicators.atr(high, low, close, atr_period)
        
        curr_close = close[-1]
        curr_upper = upper[-1]
        curr_middle = middle[-1]
        curr_lower = lower[-1]
        curr_rsi = rsi[-1]
        curr_atr = atr[-1]
        
        # Long: oversold
        if curr_close < curr_lower and curr_rsi < rsi_oversold:
            return {
                'signal': SignalType.BUY,
                'entry_price': curr_close,
                'stop_loss': curr_close - (atr_multiplier * curr_atr),
                'take_profit': curr_middle,  # Target = middle band
                'atr': curr_atr,
                'reason': f'Oversold: Close < BB Lower, RSI={curr_rsi:.1f}'
            }
        
        # Short: overbought
        elif curr_close > curr_upper and curr_rsi > rsi_overbought:
            return {
                'signal': SignalType.SELL,
                'entry_price': curr_close,
                'stop_loss': curr_close + (atr_multiplier * curr_atr),
                'take_profit': curr_middle,
                'atr': curr_atr,
                'reason': f'Overbought: Close > BB Upper, RSI={curr_rsi:.1f}'
            }
        
        return {'signal': SignalType.NO_TRADE, 'reason': 'ไม่อยู่ในโซน overbought/oversold'}


class Strategy4_RSISwing:
    """
    กลยุทธ์ 4: RSI Swing Trading
    เข้า Long: RSI < 30 แล้วกลับขึ้นตัด 30
    ออก Long: RSI > 50 หรือ RSI > 70
    """
    
    @staticmethod
    def generate_signal(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                       rsi_period: int = 14, oversold: float = 30,
                       overbought: float = 70, exit_level: float = 50,
                       atr_period: int = 14, atr_multiplier: float = 2.0) -> Dict:
        """สร้างสัญญาณจาก RSI Swing"""
        
        if len(close) < max(rsi_period, atr_period) + 2:
            return {'signal': SignalType.NO_TRADE, 'reason': 'ข้อมูลไม่เพียงพอ'}
        
        rsi = TechnicalIndicators.rsi(close, rsi_period)
        atr = TechnicalIndicators.atr(high, low, close, atr_period)
        
        prev_rsi = rsi[-2]
        curr_rsi = rsi[-1]
        curr_close = close[-1]
        curr_atr = atr[-1]
        
        # Long: RSI ตัดขึ้นจาก oversold
        if prev_rsi < oversold and curr_rsi >= oversold:
            return {
                'signal': SignalType.BUY,
                'entry_price': curr_close,
                'stop_loss': curr_close - (atr_multiplier * curr_atr),
                'take_profit': curr_close + (atr_multiplier * curr_atr * 2.5),
                'atr': curr_atr,
                'reason': f'RSI ตัดขึ้นจาก oversold ({prev_rsi:.1f} → {curr_rsi:.1f})'
            }
        
        # Short: RSI ตัดลงจาก overbought
        elif prev_rsi > overbought and curr_rsi <= overbought:
            return {
                'signal': SignalType.SELL,
                'entry_price': curr_close,
                'stop_loss': curr_close + (atr_multiplier * curr_atr),
                'take_profit': curr_close - (atr_multiplier * curr_atr * 2.5),
                'atr': curr_atr,
                'reason': f'RSI ตัดลงจาก overbought ({prev_rsi:.1f} → {curr_rsi:.1f})'
            }
        
        return {'signal': SignalType.NO_TRADE, 'reason': 'RSI ไม่อยู่ในจุด entry'}


class Strategy5_MACD:
    """
    กลยุทธ์ 5: MACD Crossover
    เข้า Long: MACD line ตัดขึ้น Signal line
    ออก Long: MACD line ตัดลง Signal line
    """
    
    @staticmethod
    def generate_signal(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                       fast: int = 12, slow: int = 26, signal_period: int = 9,
                       atr_period: int = 14, atr_multiplier: float = 2.0) -> Dict:
        """สร้างสัญญาณจาก MACD"""
        
        if len(close) < max(slow, atr_period) + signal_period + 2:
            return {'signal': SignalType.NO_TRADE, 'reason': 'ข้อมูลไม่เพียงพอ'}
        
        macd_line, signal_line, histogram = TechnicalIndicators.macd(close, fast, slow, signal_period)
        atr = TechnicalIndicators.atr(high, low, close, atr_period)
        
        prev_macd = macd_line[-2]
        prev_signal = signal_line[-2]
        curr_macd = macd_line[-1]
        curr_signal = signal_line[-1]
        curr_close = close[-1]
        curr_atr = atr[-1]
        
        # Long: MACD ตัดขึ้น Signal
        if prev_macd <= prev_signal and curr_macd > curr_signal:
            return {
                'signal': SignalType.BUY,
                'entry_price': curr_close,
                'stop_loss': curr_close - (atr_multiplier * curr_atr),
                'take_profit': curr_close + (atr_multiplier * curr_atr * 2),
                'atr': curr_atr,
                'reason': 'MACD ตัดขึ้น Signal line'
            }
        
        # Short: MACD ตัดลง Signal
        elif prev_macd >= prev_signal and curr_macd < curr_signal:
            return {
                'signal': SignalType.SELL,
                'entry_price': curr_close,
                'stop_loss': curr_close + (atr_multiplier * curr_atr),
                'take_profit': curr_close - (atr_multiplier * curr_atr * 2),
                'atr': curr_atr,
                'reason': 'MACD ตัดลง Signal line'
            }
        
        return {'signal': SignalType.NO_TRADE, 'reason': 'ไม่มี MACD crossover'}


class Strategy6_ATRTrailing:
    """
    กลยุทธ์ 6: ATR Trailing Stop
    เข้าตามเทรนด์ (ใช้ MA กรอง) และ trailing stop ด้วย ATR
    """
    
    @staticmethod
    def generate_signal(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                       atr_period: int = 14, atr_multiplier: float = 3.0,
                       trend_ma_period: int = 50) -> Dict:
        """สร้างสัญญาณจาก ATR Trailing"""
        
        if len(close) < max(atr_period, trend_ma_period) + 2:
            return {'signal': SignalType.NO_TRADE, 'reason': 'ข้อมูลไม่เพียงพอ'}
        
        atr = TechnicalIndicators.atr(high, low, close, atr_period)
        trend_ma = TechnicalIndicators.ema(close, trend_ma_period)
        
        curr_close = close[-1]
        curr_atr = atr[-1]
        curr_ma = trend_ma[-1]
        
        # Long: ราคาเหนือ MA (uptrend)
        if curr_close > curr_ma:
            return {
                'signal': SignalType.BUY,
                'entry_price': curr_close,
                'stop_loss': curr_close - (atr_multiplier * curr_atr),
                'take_profit': curr_close + (atr_multiplier * curr_atr * 3),
                'atr': curr_atr,
                'reason': f'Uptrend: Close > MA{trend_ma_period}'
            }
        
        # Short: ราคาต่ำกว่า MA (downtrend)
        elif curr_close < curr_ma:
            return {
                'signal': SignalType.SELL,
                'entry_price': curr_close,
                'stop_loss': curr_close + (atr_multiplier * curr_atr),
                'take_profit': curr_close - (atr_multiplier * curr_atr * 3),
                'atr': curr_atr,
                'reason': f'Downtrend: Close < MA{trend_ma_period}'
            }
        
        return {'signal': SignalType.NO_TRADE, 'reason': 'ไม่มีเทรนด์ชัด'}


class Strategy7_Supertrend:
    """
    กลยุทธ์ 7: Supertrend
    เข้า Long: ราคาปิดเหนือเส้น Supertrend (เปลี่ยนเป็น uptrend)
    ออก Long: ราคาปิดต่ำกว่าเส้น Supertrend (เปลี่ยนเป็น downtrend)
    """
    
    @staticmethod
    def generate_signal(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                       atr_period: int = 10, atr_multiplier: float = 3.0) -> Dict:
        """สร้างสัญญาณจาก Supertrend"""
        
        if len(close) < atr_period + 2:
            return {'signal': SignalType.NO_TRADE, 'reason': 'ข้อมูลไม่เพียงพอ'}
        
        supertrend_line, direction = TechnicalIndicators.supertrend(
            high, low, close, atr_period, atr_multiplier
        )
        atr = TechnicalIndicators.atr(high, low, close, atr_period)
        
        prev_direction = direction[-2]
        curr_direction = direction[-1]
        curr_close = close[-1]
        curr_supertrend = supertrend_line[-1]
        curr_atr = atr[-1]
        
        # เปลี่ยนจาก downtrend เป็น uptrend
        if prev_direction == -1 and curr_direction == 1:
            return {
                'signal': SignalType.BUY,
                'entry_price': curr_close,
                'stop_loss': curr_supertrend,  # Supertrend line เป็น stop
                'take_profit': curr_close + (atr_multiplier * curr_atr * 2),
                'atr': curr_atr,
                'reason': 'Supertrend เปลี่ยนเป็น Uptrend'
            }
        
        # เปลี่ยนจาก uptrend เป็น downtrend
        elif prev_direction == 1 and curr_direction == -1:
            return {
                'signal': SignalType.SELL,
                'entry_price': curr_close,
                'stop_loss': curr_supertrend,
                'take_profit': curr_close - (atr_multiplier * curr_atr * 2),
                'atr': curr_atr,
                'reason': 'Supertrend เปลี่ยนเป็น Downtrend'
            }
        
        return {'signal': SignalType.NO_TRADE, 'reason': 'Supertrend ไม่เปลี่ยนทิศ'}
