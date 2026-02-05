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
    
    @staticmethod
    def adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Average Directional Index (ADX)
        วัดความแข็งแรงของเทรนด์
        ADX > 25 = เทรนด์แข็งแกร่ง
        ADX < 20 = ไม่มีเทรนด์ชัด
        
        Returns: (di_plus, di_minus, adx)
        """
        # True Range
        tr1 = high - low
        tr2 = np.abs(high - np.roll(close, 1))
        tr3 = np.abs(low - np.roll(close, 1))
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        tr[0] = tr1[0]
        
        # Directional Movement
        dm_plus = np.where((high - np.roll(high, 1)) > (np.roll(low, 1) - low), 
                           np.maximum(high - np.roll(high, 1), 0), 0)
        dm_minus = np.where((np.roll(low, 1) - low) > (high - np.roll(high, 1)), 
                            np.maximum(np.roll(low, 1) - low, 0), 0)
        dm_plus[0] = 0
        dm_minus[0] = 0
        
        # Smooth TR and DM
        atr_smooth = pd.Series(tr).ewm(alpha=1/period, adjust=False).mean().values
        dm_plus_smooth = pd.Series(dm_plus).ewm(alpha=1/period, adjust=False).mean().values
        dm_minus_smooth = pd.Series(dm_minus).ewm(alpha=1/period, adjust=False).mean().values
        
        # Directional Indicators
        di_plus = 100 * dm_plus_smooth / (atr_smooth + 1e-10)
        di_minus = 100 * dm_minus_smooth / (atr_smooth + 1e-10)
        
        # DX and ADX
        dx = 100 * np.abs(di_plus - di_minus) / (di_plus + di_minus + 1e-10)
        adx = pd.Series(dx).ewm(alpha=1/period, adjust=False).mean().values
        
        return di_plus, di_minus, adx
    
    @staticmethod
    def ichimoku(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                 tenkan_period: int = 9, kijun_period: int = 26, 
                 senkou_b_period: int = 52) -> Dict[str, np.ndarray]:
        """
        Ichimoku Cloud (Japanese Equilibrium Theory)
        
        Returns: {
            'tenkan_sen': Conversion Line,
            'kijun_sen': Base Line,
            'senkou_span_a': Leading Span A,
            'senkou_span_b': Leading Span B,
            'chikou_span': Lagging Span
        }
        """
        # Tenkan-sen (Conversion Line)
        tenkan_high = pd.Series(high).rolling(window=tenkan_period).max().values
        tenkan_low = pd.Series(low).rolling(window=tenkan_period).min().values
        tenkan_sen = (tenkan_high + tenkan_low) / 2
        
        # Kijun-sen (Base Line)
        kijun_high = pd.Series(high).rolling(window=kijun_period).max().values
        kijun_low = pd.Series(low).rolling(window=kijun_period).min().values
        kijun_sen = (kijun_high + kijun_low) / 2
        
        # Senkou Span A (Leading Span A) - shifted forward
        senkou_span_a = (tenkan_sen + kijun_sen) / 2
        
        # Senkou Span B (Leading Span B) - shifted forward
        senkou_b_high = pd.Series(high).rolling(window=senkou_b_period).max().values
        senkou_b_low = pd.Series(low).rolling(window=senkou_b_period).min().values
        senkou_span_b = (senkou_b_high + senkou_b_low) / 2
        
        # Chikou Span (Lagging Span) - shifted backward
        chikou_span = close
        
        return {
            'tenkan_sen': tenkan_sen,
            'kijun_sen': kijun_sen,
            'senkou_span_a': senkou_span_a,
            'senkou_span_b': senkou_span_b,
            'chikou_span': chikou_span
        }
    
    @staticmethod
    def vwap(high: np.ndarray, low: np.ndarray, close: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """
        Volume Weighted Average Price
        VWAP = Σ(Price × Volume) / Σ(Volume)
        """
        typical_price = (high + low + close) / 3
        cumulative_tp_volume = np.cumsum(typical_price * volume)
        cumulative_volume = np.cumsum(volume)
        
        vwap = cumulative_tp_volume / (cumulative_volume + 1e-10)
        return vwap
    
    @staticmethod
    def mfi(high: np.ndarray, low: np.ndarray, close: np.ndarray, 
            volume: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Money Flow Index (Volume-weighted RSI)
        MFI = 100 - (100 / (1 + Money Ratio))
        """
        typical_price = (high + low + close) / 3
        money_flow = typical_price * volume
        
        # Positive and Negative Money Flow
        positive_flow = np.where(typical_price > np.roll(typical_price, 1), money_flow, 0)
        negative_flow = np.where(typical_price < np.roll(typical_price, 1), money_flow, 0)
        positive_flow[0] = 0
        negative_flow[0] = 0
        
        # Sum over period
        positive_mf = pd.Series(positive_flow).rolling(window=period).sum().values
        negative_mf = pd.Series(negative_flow).rolling(window=period).sum().values
        
        # Money Ratio and MFI
        money_ratio = positive_mf / (negative_mf + 1e-10)
        mfi = 100 - (100 / (1 + money_ratio))
        
        return mfi
    
    @staticmethod
    def fibonacci_retracement(high_price: float, low_price: float) -> Dict[str, float]:
        """
        Fibonacci Retracement Levels
        คำนวณระดับ Fibonacci จากจุดสูงสุดและต่ำสุด
        
        Returns: dict of fib levels
        """
        diff = high_price - low_price
        
        return {
            'level_0': high_price,
            'level_236': high_price - (diff * 0.236),
            'level_382': high_price - (diff * 0.382),
            'level_500': high_price - (diff * 0.500),
            'level_618': high_price - (diff * 0.618),
            'level_786': high_price - (diff * 0.786),
            'level_100': low_price
        }
    
    @staticmethod
    def linear_regression(data: np.ndarray, period: int = 50) -> Tuple[np.ndarray, float]:
        """
        Linear Regression
        หาเส้นแนวโน้มเชิงเส้นและความชัน
        
        Returns: (regression_line, slope)
        """
        linreg = pd.Series(data).rolling(window=period).apply(
            lambda x: np.polyfit(np.arange(len(x)), x, 1)[1], raw=True
        ).values
        
        # คำนวณความชัน
        if len(data) >= period:
            slope = (linreg[-1] - linreg[-2]) / linreg[-2] * 100 if linreg[-2] != 0 else 0
        else:
            slope = 0
        
        return linreg, slope
    
    @staticmethod
    def hurst_exponent(data: np.ndarray, max_lag: int = 20) -> float:
        """
        Hurst Exponent - วัดความต่อเนื่องของเทรนด์
        H > 0.5 = trending (persistent)
        H = 0.5 = random walk
        H < 0.5 = mean reverting (anti-persistent)
        """
        if len(data) < max_lag * 2:
            return 0.5
        
        lags = range(2, max_lag)
        tau = []
        
        for lag in lags:
            # Calculate standard deviation of differences
            pp = np.subtract(data[lag:], data[:-lag])
            tau.append(np.std(pp))
        
        # Linear regression on log-log plot
        tau = np.array(tau)
        lags = np.array(list(lags))
        
        # Filter out zeros
        valid = tau > 0
        if np.sum(valid) < 2:
            return 0.5
        
        poly = np.polyfit(np.log(lags[valid]), np.log(tau[valid]), 1)
        hurst = poly[0]
        
        return np.clip(hurst, 0, 1)
    
    @staticmethod
    def kalman_filter(data: np.ndarray, process_noise: float = 0.01, 
                     measurement_noise: float = 0.1) -> np.ndarray:
        """
        Kalman Filter - กรองสัญญาณรบกวน
        ให้ค่าประมาณที่ดีที่สุดของราคาที่แท้จริง
        """
        n = len(data)
        kalman_estimate = np.zeros(n)
        kalman_error = np.ones(n)
        
        kalman_estimate[0] = data[0]
        kalman_error[0] = 1.0
        
        for i in range(1, n):
            # Kalman Gain
            kalman_gain = kalman_error[i-1] / (kalman_error[i-1] + measurement_noise)
            
            # Update estimate
            kalman_estimate[i] = kalman_estimate[i-1] + kalman_gain * (data[i] - kalman_estimate[i-1])
            
            # Update error
            kalman_error[i] = (1 - kalman_gain) * kalman_error[i-1] + process_noise
        
        return kalman_estimate


class CandlestickPatterns:
    """คลาสสำหรับตรวจจับรูปแบบแท่งเทียน"""
    
    @staticmethod
    def is_doji(open_: float, high: float, low: float, close: float) -> bool:
        """Doji - ตัวเทียนมี body เล็กมาก"""
        body = abs(close - open_)
        range_ = high - low
        return body <= range_ * 0.1 if range_ > 0 else False
    
    @staticmethod
    def is_hammer(open_: float, high: float, low: float, close: float) -> bool:
        """Hammer - แท่งเทียนที่มีหาง shadow ล่างยาว"""
        body = abs(close - open_)
        range_ = high - low
        lower_shadow = min(open_, close) - low
        upper_shadow = high - max(open_, close)
        
        return (range_ > 3 * body and 
                lower_shadow > 0.6 * range_ and 
                upper_shadow < 0.3 * range_) if range_ > 0 else False
    
    @staticmethod
    def is_shooting_star(open_: float, high: float, low: float, close: float) -> bool:
        """Shooting Star - แท่งเทียนที่มีหาง shadow บนยาว"""
        body = abs(close - open_)
        range_ = high - low
        lower_shadow = min(open_, close) - low
        upper_shadow = high - max(open_, close)
        
        return (range_ > 3 * body and 
                upper_shadow > 0.6 * range_ and 
                lower_shadow < 0.3 * range_) if range_ > 0 else False
    
    @staticmethod
    def is_bullish_engulfing(open_1: float, close_1: float, 
                            open_2: float, close_2: float) -> bool:
        """Bullish Engulfing - แท่งเขียวครอบแท่งแดง"""
        return (close_1 < open_1 and  # แท่งก่อนหน้าเป็นแดง
                close_2 > open_2 and  # แท่งปัจจุบันเป็นเขียว
                close_2 > open_1 and  # ปิดเหนือ open แท่งก่อน
                open_2 < close_1)     # เปิดต่ำกว่า close แท่งก่อน
    
    @staticmethod
    def is_bearish_engulfing(open_1: float, close_1: float, 
                            open_2: float, close_2: float) -> bool:
        """Bearish Engulfing - แท่งแดงครอบแท่งเขียว"""
        return (close_1 > open_1 and  # แท่งก่อนหน้าเป็นเขียว
                close_2 < open_2 and  # แท่งปัจจุบันเป็นแดง
                close_2 < open_1 and  # ปิดต่ำกว่า open แท่งก่อน
                open_2 > close_1)     # เปิดสูงกว่า close แท่งก่อน
    
    @staticmethod
    def is_morning_star(open_1: float, close_1: float,
                       open_2: float, high_2: float, low_2: float, close_2: float,
                       open_3: float, close_3: float) -> bool:
        """Morning Star - 3 แท่ง: แดง, Doji, เขียว"""
        doji = CandlestickPatterns.is_doji(open_2, high_2, low_2, close_2)
        return (close_1 < open_1 and  # แท่งแรกแดง
                doji and              # แท่งกลาง Doji
                close_3 > open_3 and  # แท่งสุดท้ายเขียว
                close_3 > (open_1 + close_1) / 2)  # ปิดเหนือกึ่งกลางแท่งแรก
    
    @staticmethod
    def is_evening_star(open_1: float, close_1: float,
                       open_2: float, high_2: float, low_2: float, close_2: float,
                       open_3: float, close_3: float) -> bool:
        """Evening Star - 3 แท่ง: เขียว, Doji, แดง"""
        doji = CandlestickPatterns.is_doji(open_2, high_2, low_2, close_2)
        return (close_1 > open_1 and  # แท่งแรกเขียว
                doji and              # แท่งกลาง Doji
                close_3 < open_3 and  # แท่งสุดท้ายแดง
                close_3 < (open_1 + close_1) / 2)  # ปิดต่ำกว่ากึ่งกลางแท่งแรก


class AIPatternRecognition:
    """ระบบ AI สำหรับการรู้จำรูปแบบและวิเคราะห์ตลาด"""
    
    @staticmethod
    def detect_divergence(price: np.ndarray, indicator: np.ndarray, 
                         lookback: int = 5) -> Dict[str, bool]:
        """
        ตรวจจับ Divergence ระหว่างราคากับ indicator
        
        Returns: {'bullish': bool, 'bearish': bool}
        """
        if len(price) < lookback + 1 or len(indicator) < lookback + 1:
            return {'bullish': False, 'bearish': False}
        
        # หาจุดต่ำสุดและสูงสุดของราคา
        price_low_1 = np.min(price[-lookback-1:-1])
        price_low_2 = price[-1]
        price_high_1 = np.max(price[-lookback-1:-1])
        price_high_2 = price[-1]
        
        # หาจุดต่ำสุดและสูงสุดของ indicator
        ind_low_1 = np.min(indicator[-lookback-1:-1])
        ind_low_2 = indicator[-1]
        ind_high_1 = np.max(indicator[-lookback-1:-1])
        ind_high_2 = indicator[-1]
        
        # Bullish Divergence: ราคาต่ำลง แต่ indicator สูงขึ้น
        bullish_div = (price_low_2 < price_low_1 and ind_low_2 > ind_low_1)
        
        # Bearish Divergence: ราคาสูงขึ้น แต่ indicator ต่ำลง
        bearish_div = (price_high_2 > price_high_1 and ind_high_2 < ind_high_1)
        
        return {'bullish': bullish_div, 'bearish': bearish_div}
    
    @staticmethod
    def market_regime_detection(close: np.ndarray, lookback: int = 50) -> str:
        """
        ตรวจจับสภาวะตลาด (Market Regime)
        
        Returns: 'trending', 'volatile', 'ranging', 'crisis'
        """
        if len(close) < lookback:
            return 'unknown'
        
        returns = np.diff(np.log(close[-lookback:]))
        avg_return = np.mean(returns)
        return_std = np.std(returns)
        
        # Sharpe Ratio แบบง่าย
        sharpe_ratio = avg_return / (return_std + 1e-10)
        
        if sharpe_ratio > 0.5:
            return 'trending'
        elif sharpe_ratio > 0:
            return 'volatile'
        elif sharpe_ratio > -0.5:
            return 'ranging'
        else:
            return 'crisis'
    
    @staticmethod
    def volume_price_correlation(close: np.ndarray, volume: np.ndarray, 
                                 period: int = 20) -> Tuple[float, str]:
        """
        วิเคราะห์ความสัมพันธ์ระหว่างราคาและปริมาณ
        
        Returns: (correlation, strength)
        """
        if len(close) < period + 1 or len(volume) < period + 1:
            return 0.0, 'unknown'
        
        price_change = np.diff(close[-period-1:])
        volume_change = np.diff(volume[-period-1:])
        
        # คำนวณ Pearson Correlation
        if np.std(price_change) > 0 and np.std(volume_change) > 0:
            correlation = np.corrcoef(price_change, volume_change)[0, 1]
        else:
            correlation = 0.0
        
        # ประเมินความแข็งแกร่ง
        abs_corr = abs(correlation)
        if abs_corr > 0.7:
            strength = 'very_strong'
        elif abs_corr > 0.5:
            strength = 'strong'
        elif abs_corr > 0.3:
            strength = 'moderate'
        else:
            strength = 'weak'
        
        return correlation, strength
    
    @staticmethod
    def momentum_quality_index(close: np.ndarray, high: np.ndarray, 
                              low: np.ndarray, volume: np.ndarray) -> float:
        """
        Momentum Quality Index - รวมหลาย momentum indicators
        
        Returns: 0-1 (0 = weak, 1 = strong)
        """
        if len(close) < 20:
            return 0.5
        
        # RSI component
        rsi = TechnicalIndicators.rsi(close, 14)
        rsi_score = rsi[-1] / 100.0
        
        # Stochastic component
        lowest_low = np.min(low[-14:])
        highest_high = np.max(high[-14:])
        stoch_k = (close[-1] - lowest_low) / (highest_high - lowest_low + 1e-10)
        
        # MFI component (simplified)
        if len(volume) >= len(close):
            typical_price = (high + low + close) / 3
            money_flow = typical_price * volume
            mfi_score = min(money_flow[-1] / (np.mean(money_flow[-14:]) + 1e-10), 2.0) / 2.0
        else:
            mfi_score = 0.5
        
        # Combined score
        momentum_quality = (rsi_score * 0.4 + stoch_k * 0.3 + mfi_score * 0.3)
        
        return np.clip(momentum_quality, 0, 1)


class ProbabilityModels:
    """โมเดลความน่าจะเป็นขั้นสูง"""
    
    @staticmethod
    def bayesian_probability(prior_up: float, prior_down: float,
                           likelihood_up: float, likelihood_down: float) -> Tuple[float, float]:
        """
        Bayesian Probability Update
        P(A|B) = P(B|A) × P(A) / P(B)
        
        Args:
            prior_up: ความน่าจะเป็นก่อนหน้าที่ราคาจะขึ้น (0-1)
            prior_down: ความน่าจะเป็นก่อนหน้าที่ราคาจะลง (0-1)
            likelihood_up: โอกาสที่จะเห็นสัญญาณปัจจุบันถ้าตลาดจะขึ้น (0-1)
            likelihood_down: โอกาสที่จะเห็นสัญญาณปัจจุบันถ้าตลาดจะลง (0-1)
        
        Returns: (posterior_up, posterior_down)
        """
        # Evidence (ความน่าจะเป็นที่จะเห็นสัญญาณนี้)
        evidence = (likelihood_up * prior_up) + (likelihood_down * prior_down)
        
        if evidence == 0:
            return prior_up, prior_down
        
        # Posterior probability
        posterior_up = (likelihood_up * prior_up) / evidence
        posterior_down = (likelihood_down * prior_down) / evidence
        
        return posterior_up, posterior_down
    
    @staticmethod
    def conditional_probability(data: np.ndarray, condition_func, 
                               outcome_func, lookback: int = 50) -> float:
        """
        Conditional Probability
        P(A|B) = จำนวนครั้งที่ A และ B เกิดขึ้น / จำนวนครั้งที่ B เกิดขึ้น
        
        Args:
            data: ข้อมูลราคา
            condition_func: ฟังก์ชันตรวจสอบเงื่อนไข B
            outcome_func: ฟังก์ชันตรวจสอบผลลัพธ์ A
            lookback: จำนวนแท่งที่ใช้คำนวณ
        
        Returns: ความน่าจะเป็น (0-1)
        """
        if len(data) < lookback + 2:
            return 0.5
        
        condition_count = 0
        outcome_given_condition = 0
        
        for i in range(len(data) - lookback - 1, len(data) - 1):
            if condition_func(data, i):
                condition_count += 1
                if outcome_func(data, i + 1):
                    outcome_given_condition += 1
        
        if condition_count == 0:
            return 0.5
        
        return outcome_given_condition / condition_count
    
    @staticmethod
    def growth_rate_forecast(close: np.ndarray, periods_back: int = 20,
                           periods_forward: int = 5) -> Tuple[float, float]:
        """
        Growth Rate Analysis & Projection
        คำนวณอัตราการเติบโตและคาดการณ์ราคา
        
        Returns: (growth_rate_percent, projected_return_percent)
        """
        if len(close) < periods_back + 1:
            return 0.0, 0.0
        
        current_price = close[-1]
        past_price = close[-periods_back-1]
        
        if past_price == 0:
            return 0.0, 0.0
        
        # Growth rate per period
        growth_rate = (current_price / past_price) ** (1.0 / periods_back) - 1
        growth_rate_percent = growth_rate * 100
        
        # Projected price
        projected_price = current_price * ((1 + growth_rate) ** periods_forward)
        projected_return_percent = ((projected_price - current_price) / current_price) * 100
        
        return growth_rate_percent, projected_return_percent
    
    @staticmethod
    def exponential_weighted_probability(current_prob: float, past_ewma: float,
                                       alpha: float = 0.3) -> float:
        """
        Exponential Weighted Moving Average of Probability
        ให้น้ำหนักกับข้อมูลล่าสุดมากกว่า
        
        EWMA_t = α × X_t + (1-α) × EWMA_{t-1}
        """
        ewma = alpha * current_prob + (1 - alpha) * past_ewma
        return ewma


class UltimateAccuracyScore:
    """
    ระบบคำนวณความแม่นยำสูงสุด (Ultimate Accuracy Score)
    รวมทุกทฤษฎีการเทรดมาคำนวณความน่าจะเป็นที่แม่นยำที่สุด
    """
    
    @staticmethod
    def calculate_short_term_probability(high: np.ndarray, low: np.ndarray, 
                                        close: np.ndarray, volume: Optional[np.ndarray] = None) -> Dict:
        """คำนวณความน่าจะเป็นระยะสั้น (6 ปัจจัย)"""
        
        if len(close) < 30:
            return {'probability_up': 50.0, 'probability_down': 50.0, 'confidence': 0.0}
        
        scores = []
        
        # 1. Trend Momentum (25%)
        ma = TechnicalIndicators.sma(close, 20)
        trend_score = 25.0 if close[-1] > ma[-1] else 0.0
        scores.append(trend_score)
        
        # 2. RSI Momentum (20%)
        rsi = TechnicalIndicators.rsi(close, 14)
        if rsi[-1] < 30:
            rsi_score = 20.0
        elif rsi[-1] < 40:
            rsi_score = 15.0
        elif rsi[-1] > 70:
            rsi_score = 0.0
        elif rsi[-1] > 60:
            rsi_score = 5.0
        else:
            rsi_score = 10.0
        scores.append(rsi_score)
        
        # 3. Volume Confirmation (15%)
        if volume is not None and len(volume) == len(close):
            avg_volume = np.mean(volume[-20:])
            volume_ratio = volume[-1] / (avg_volume + 1e-10)
            is_bullish_candle = close[-1] > close[-2]
            
            if volume_ratio > 1.5 and is_bullish_candle:
                volume_score = 15.0
            elif volume_ratio > 1.2 and is_bullish_candle:
                volume_score = 10.0
            elif volume_ratio < 0.8:
                volume_score = 0.0
            else:
                volume_score = 7.5
        else:
            volume_score = 7.5
        scores.append(volume_score)
        
        # 4. Bollinger Bands Position (15%)
        upper, middle, lower = TechnicalIndicators.bollinger_bands(close, 20, 2.0)
        bb_range = upper[-1] - lower[-1]
        if bb_range > 0:
            bb_position = (close[-1] - lower[-1]) / bb_range
            if bb_position < 0.2:
                bb_score = 15.0
            elif bb_position < 0.4:
                bb_score = 12.0
            elif bb_position > 0.8:
                bb_score = 0.0
            elif bb_position > 0.6:
                bb_score = 3.0
            else:
                bb_score = 7.5
        else:
            bb_score = 7.5
        scores.append(bb_score)
        
        # 5. Price Action Pattern (15%)
        bullish_candle = close[-1] > close[-2]
        consecutive_green = bullish_candle and close[-2] > close[-3]
        consecutive_red = not bullish_candle and close[-2] < close[-3]
        
        if consecutive_green:
            pattern_score = 15.0
        elif bullish_candle:
            pattern_score = 10.0
        elif consecutive_red:
            pattern_score = 0.0
        else:
            pattern_score = 5.0
        scores.append(pattern_score)
        
        # 6. MACD Momentum (10%)
        macd_line, signal_line, _ = TechnicalIndicators.macd(close, 12, 26, 9)
        macd_bullish = macd_line[-1] > signal_line[-1]
        
        if macd_bullish and macd_line[-1] > 0:
            macd_score = 10.0
        elif macd_bullish:
            macd_score = 7.5
        elif macd_line[-1] < 0 and macd_line[-1] < signal_line[-1]:
            macd_score = 0.0
        else:
            macd_score = 5.0
        scores.append(macd_score)
        
        # รวมคะแนน
        total_score = sum(scores)
        probability_up = total_score
        probability_down = 100 - total_score
        confidence = abs(probability_up - 50) * 2
        
        return {
            'probability_up': probability_up,
            'probability_down': probability_down,
            'confidence': confidence,
            'scores': {
                'trend': scores[0],
                'rsi': scores[1],
                'volume': scores[2],
                'bollinger': scores[3],
                'pattern': scores[4],
                'macd': scores[5]
            }
        }
    
    @staticmethod
    def calculate_long_term_probability(high: np.ndarray, low: np.ndarray,
                                       close: np.ndarray, volume: Optional[np.ndarray] = None) -> Dict:
        """คำนวณความน่าจะเป็นระยะยาว (6 ปัจจัย)"""
        
        if len(close) < 100:
            # ถ้าข้อมูลน้อยกว่า 200 แท่ง ใช้ค่าที่มีแทน
            return {'probability_up': 50.0, 'probability_down': 50.0, 'confidence': 0.0, 'trend_strength': 'unknown'}
        
        scores = []
        
        # 1. Long-term Trend (30%)
        # ปรับให้ใช้ MA ที่สั้นกว่าถ้าข้อมูลไม่พอ
        ma_period_1 = min(50, len(close) - 10)
        ma_period_2 = min(100, len(close) - 5)  # ใช้ 100 แทน 200
        
        if ma_period_1 < 20 or ma_period_2 < 50:
            # ข้อมูลน้อยเกินไป ใช้ค่า default
            lt_trend_score = 10.0
            scores.append(lt_trend_score)
        else:
            ma_50 = TechnicalIndicators.sma(close, ma_period_1)
            ma_200 = TechnicalIndicators.sma(close, ma_period_2)
        
            if close[-1] > ma_50[-1] and ma_50[-1] > ma_200[-1]:
                lt_trend_score = 30.0
            elif close[-1] > ma_50[-1]:
                lt_trend_score = 20.0
            elif close[-1] < ma_50[-1] and ma_50[-1] < ma_200[-1]:
                lt_trend_score = 0.0
            else:
                lt_trend_score = 10.0
            scores.append(lt_trend_score)
        
        # 2. Long-term RSI (20%)
        rsi = TechnicalIndicators.rsi(close, 21)
        if rsi[-1] < 35:
            lt_rsi_score = 20.0
        elif rsi[-1] < 45:
            lt_rsi_score = 15.0
        elif rsi[-1] > 65:
            lt_rsi_score = 0.0
        elif rsi[-1] > 55:
            lt_rsi_score = 5.0
        else:
            lt_rsi_score = 10.0
        scores.append(lt_rsi_score)
        
        # 3. Price Position vs Historical Range (15%)
        highest_100 = np.max(high[-100:])
        lowest_100 = np.min(low[-100:])
        price_range = highest_100 - lowest_100
        
        if price_range > 0:
            price_position = (close[-1] - lowest_100) / price_range
            if price_position < 0.25:
                position_score = 15.0
            elif price_position < 0.4:
                position_score = 12.0
            elif price_position > 0.75:
                position_score = 0.0
            elif price_position > 0.6:
                position_score = 3.0
            else:
                position_score = 7.5
        else:
            position_score = 7.5
        scores.append(position_score)
        
        # 4. Long-term Volume Trend (10%)
        if volume is not None and len(volume) >= 50:
            volume_ma_50 = np.mean(volume[-50:])
            volume_ma_10 = np.mean(volume[-10:])
            volume_trend = volume_ma_10 > volume_ma_50
            is_bullish = close[-1] > close[-2]
            
            if volume_trend and is_bullish:
                lt_volume_score = 10.0
            elif volume_trend:
                lt_volume_score = 7.0
            else:
                lt_volume_score = 3.0
        else:
            lt_volume_score = 5.0
        scores.append(lt_volume_score)
        
        # 5. ADX (15%)
        _, _, adx = TechnicalIndicators.adx(high, low, close, 14)
        di_plus, di_minus, _ = TechnicalIndicators.adx(high, low, close, 14)
        
        if adx[-1] > 25 and di_plus[-1] > di_minus[-1]:
            adx_score = 15.0
        elif adx[-1] > 25 and di_minus[-1] > di_plus[-1]:
            adx_score = 0.0
        elif di_plus[-1] > di_minus[-1]:
            adx_score = 10.0
        else:
            adx_score = 5.0
        scores.append(adx_score)
        
        # 6. Long-term MACD (10%)
        macd_line, signal_line, _ = TechnicalIndicators.macd(close, 26, 52, 18)
        
        if macd_line[-1] > signal_line[-1] and macd_line[-1] > 0:
            lt_macd_score = 10.0
        elif macd_line[-1] > signal_line[-1]:
            lt_macd_score = 7.0
        elif macd_line[-1] < signal_line[-1] and macd_line[-1] < 0:
            lt_macd_score = 0.0
        else:
            lt_macd_score = 3.0
        scores.append(lt_macd_score)
        
        # รวมคะแนน
        total_score = sum(scores)
        probability_up = total_score
        probability_down = 100 - total_score
        confidence = abs(probability_up - 50) * 2
        
        return {
            'probability_up': probability_up,
            'probability_down': probability_down,
            'confidence': confidence,
            'trend_strength': 'strong' if adx[-1] > 25 else 'weak'
        }
    
    @staticmethod
    def calculate_ultimate_score(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                                volume: Optional[np.ndarray] = None) -> Dict:
        """
        คำนวณ Ultimate Accuracy Score
        รวมทุกปัจจัยเพื่อให้ความแม่นยำสูงสุด
        (ปรับให้ทำงานได้กับข้อมูล 100 แท่งขึ้นไป)
        """
        
        if len(close) < 100:
            return {
                'ultimate_accuracy': 50.0,
                'confidence_level': 'very_low',
                'direction': 'neutral',
                'recommendation': 'wait',
                'error': f'ข้อมูลไม่เพียงพอ (มี {len(close)} แท่ง, ต้องการอย่างน้อย 100 แท่ง)'
            }
        
        # 1. Short-term Probability (30%)
        short_term = UltimateAccuracyScore.calculate_short_term_probability(high, low, close, volume)
        
        # 2. Long-term Probability (30%)
        long_term = UltimateAccuracyScore.calculate_long_term_probability(high, low, close, volume)
        
        # 3. AI Pattern Recognition (20%)
        # Candlestick patterns
        bullish_pattern_score = 0
        bearish_pattern_score = 0
        
        if len(close) >= 3:
            if CandlestickPatterns.is_hammer(close[-2], high[-1], low[-1], close[-1]):
                bullish_pattern_score += 15
            if CandlestickPatterns.is_bullish_engulfing(close[-2], close[-1], close[-2], close[-1]):
                bullish_pattern_score += 20
            if CandlestickPatterns.is_shooting_star(close[-2], high[-1], low[-1], close[-1]):
                bearish_pattern_score += 15
            if CandlestickPatterns.is_bearish_engulfing(close[-2], close[-1], close[-2], close[-1]):
                bearish_pattern_score += 20
        
        pattern_confidence = max(bullish_pattern_score, bearish_pattern_score)
        
        # Market Regime
        regime = AIPatternRecognition.market_regime_detection(close, 50)
        regime_score = 25 if regime == 'trending' else 10 if regime == 'volatile' else 0
        
        ai_score = (pattern_confidence + regime_score) / 50 * 100  # normalize to 0-100
        
        # 4. Fibonacci & Technical Levels (10%)
        highest = np.max(high[-100:])
        lowest = np.min(low[-100:])
        fib_levels = TechnicalIndicators.fibonacci_retracement(highest, lowest)
        
        # ตรวจสอบว่าราคาใกล้ระดับ Fibonacci หรือไม่
        atr = TechnicalIndicators.atr(high, low, close, 14)
        near_fib = False
        for level_name, level_value in fib_levels.items():
            if abs(close[-1] - level_value) < atr[-1] * 0.5:
                near_fib = True
                break
        
        fib_score = 25.0 if near_fib else 10.0
        
        # 5. Hurst Exponent (5%)
        hurst = TechnicalIndicators.hurst_exponent(close, min(20, len(close) - 5))
        hurst_score = 20.0 if hurst > 0.5 else 10.0 if hurst < 0.5 else 15.0
        
        # 6. Ichimoku (5%) - ปรับให้ทำงานกับข้อมูลน้อยกว่า
        ichimoku_periods = [min(9, len(close) // 10), min(26, len(close) // 5), min(52, len(close) // 2)]
        if ichimoku_periods[2] < 30:
            # ข้อมูลน้อยเกินไป ข้าม Ichimoku
            ichimoku_score = 12.5
        else:
            ichimoku = TechnicalIndicators.ichimoku(high, low, close, ichimoku_periods[0], ichimoku_periods[1], ichimoku_periods[2])
            cloud_top = max(ichimoku['senkou_span_a'][-1], ichimoku['senkou_span_b'][-1])
            cloud_bottom = min(ichimoku['senkou_span_a'][-1], ichimoku['senkou_span_b'][-1])
            above_cloud = close[-1] > cloud_top
            below_cloud = close[-1] < cloud_bottom
            ichimoku_score = 25.0 if above_cloud else 0.0 if below_cloud else 12.5
        
        # คำนวณ Composite Accuracy
        composite_accuracy = (
            short_term['probability_up'] * 0.30 +
            long_term['probability_up'] * 0.30 +
            ai_score * 0.20 +
            fib_score * 0.10 +
            hurst_score * 0.05 +
            ichimoku_score * 0.05
        )
        
        # คำนวณ Ultimate Accuracy
        ultimate_accuracy = min(composite_accuracy, 100.0)
        
        # ระดับความมั่นใจ
        if ultimate_accuracy >= 90:
            confidence_level = 'very_high'
        elif ultimate_accuracy >= 75:
            confidence_level = 'high'
        elif ultimate_accuracy >= 60:
            confidence_level = 'medium'
        elif ultimate_accuracy >= 45:
            confidence_level = 'low'
        else:
            confidence_level = 'very_low'
        
        # ทิศทางและคำแนะนำ
        if ultimate_accuracy >= 70 and composite_accuracy > 65:
            direction = 'strong_buy' if short_term['probability_up'] > 60 else 'strong_sell'
            recommendation = 'strong_buy' if short_term['probability_up'] > 60 else 'strong_sell'
        elif composite_accuracy > 50:
            direction = 'buy' if short_term['probability_up'] > 50 else 'sell'
            recommendation = 'buy' if short_term['probability_up'] > 50 else 'sell'
        else:
            direction = 'neutral'
            recommendation = 'wait'
        
        return {
            'ultimate_accuracy': round(ultimate_accuracy, 2),
            'confidence_level': confidence_level,
            'direction': direction,
            'recommendation': recommendation,
            'short_term': short_term,
            'long_term': long_term,
            'ai_score': round(ai_score, 2),
            'composite_accuracy': round(composite_accuracy, 2),
            'market_regime': regime,
            'hurst_exponent': round(hurst, 3)
        }


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


class Strategy8_UltimateAccuracy:
    """
    กลยุทธ์ 8: Ultimate Accuracy Strategy
    ใช้ระบบ Ultimate Accuracy Score รวมทุกทฤษฎีการเทรด
    เทรดเฉพาะเมื่อความแม่นยำสูง (≥75%)
    """
    
    @staticmethod
    def generate_signal(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                       volume: Optional[np.ndarray] = None,
                       atr_period: int = 14, atr_multiplier: float = 2.0,
                       min_accuracy: float = 75.0) -> Dict:
        """
        สร้างสัญญาณจาก Ultimate Accuracy Score
        
        Args:
            min_accuracy: ความแม่นยำขั้นต่ำที่ยอมรับ (default 75%)
        """
        
        if len(close) < 100:
            return {'signal': SignalType.NO_TRADE, 'reason': f'ข้อมูลไม่เพียงพอ (มี {len(close)} แท่ง, ต้องการอย่างน้อย 100 แท่ง)'}
        
        # คำนวณ Ultimate Accuracy Score
        ultimate = UltimateAccuracyScore.calculate_ultimate_score(high, low, close, volume)
        
        # คำนวณ ATR สำหรับ SL/TP
        atr = TechnicalIndicators.atr(high, low, close, atr_period)
        curr_close = close[-1]
        curr_atr = atr[-1]
        
        # ตรวจสอบว่าความแม่นยำสูงพอหรือไม่
        if ultimate['ultimate_accuracy'] < min_accuracy:
            return {
                'signal': SignalType.NO_TRADE,
                'reason': f"ความแม่นยำต่ำเกินไป ({ultimate['ultimate_accuracy']:.1f}% < {min_accuracy}%)",
                'ultimate_data': ultimate
            }
        
        # ตัดสินใจตามคำแนะนำ
        recommendation = ultimate['recommendation']
        
        if recommendation == 'strong_buy':
            # Strong Buy Signal
            return {
                'signal': SignalType.BUY,
                'entry_price': curr_close,
                'stop_loss': curr_close - (atr_multiplier * curr_atr),
                'take_profit': curr_close + (atr_multiplier * curr_atr * 3),  # RR 1:3
                'atr': curr_atr,
                'reason': f"Ultimate: STRONG BUY | Accuracy: {ultimate['ultimate_accuracy']:.1f}% | {ultimate['confidence_level']} confidence",
                'ultimate_data': ultimate
            }
        
        elif recommendation == 'buy':
            # Buy Signal
            return {
                'signal': SignalType.BUY,
                'entry_price': curr_close,
                'stop_loss': curr_close - (atr_multiplier * curr_atr),
                'take_profit': curr_close + (atr_multiplier * curr_atr * 2),  # RR 1:2
                'atr': curr_atr,
                'reason': f"Ultimate: BUY | Accuracy: {ultimate['ultimate_accuracy']:.1f}% | {ultimate['confidence_level']}",
                'ultimate_data': ultimate
            }
        
        elif recommendation == 'strong_sell':
            # Strong Sell Signal
            return {
                'signal': SignalType.SELL,
                'entry_price': curr_close,
                'stop_loss': curr_close + (atr_multiplier * curr_atr),
                'take_profit': curr_close - (atr_multiplier * curr_atr * 3),  # RR 1:3
                'atr': curr_atr,
                'reason': f"Ultimate: STRONG SELL | Accuracy: {ultimate['ultimate_accuracy']:.1f}% | {ultimate['confidence_level']} confidence",
                'ultimate_data': ultimate
            }
        
        elif recommendation == 'sell':
            # Sell Signal
            return {
                'signal': SignalType.SELL,
                'entry_price': curr_close,
                'stop_loss': curr_close + (atr_multiplier * curr_atr),
                'take_profit': curr_close - (atr_multiplier * curr_atr * 2),  # RR 1:2
                'atr': curr_atr,
                'reason': f"Ultimate: SELL | Accuracy: {ultimate['ultimate_accuracy']:.1f}% | {ultimate['confidence_level']}",
                'ultimate_data': ultimate
            }
        
        else:
            # Wait/Neutral
            return {
                'signal': SignalType.NO_TRADE,
                'reason': f"Ultimate: WAIT | Accuracy: {ultimate['ultimate_accuracy']:.1f}% | สัญญาณไม่ชัดเจน",
                'ultimate_data': ultimate
            }


class Strategy9_AIMultiFactor:
    """
    กลยุทธ์ 9: AI Multi-Factor Strategy
    รวม AI Pattern Recognition + Probability Models + Advanced Indicators
    """
    
    @staticmethod
    def generate_signal(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                       volume: Optional[np.ndarray] = None,
                       atr_period: int = 14, atr_multiplier: float = 2.0) -> Dict:
        """
        สร้างสัญญาณจาก AI Multi-Factor Analysis
        (ปรับปรุงให้ทำงานได้ดีขึ้น พร้อม debug info)
        """
        
        if len(close) < 100:
            return {'signal': SignalType.NO_TRADE, 'reason': f'ข้อมูลไม่เพียงพอ (มี {len(close)} แท่ง, ต้องการ 100 แท่ง)'}
        
        # คำนวณ indicators
        rsi = TechnicalIndicators.rsi(close, 14)
        atr = TechnicalIndicators.atr(high, low, close, atr_period)
        di_plus, di_minus, adx = TechnicalIndicators.adx(high, low, close, 14)
        
        curr_close = close[-1]
        curr_atr = atr[-1]
        
        # เก็บ debug info
        debug_info = {}
        
        # 1. AI Pattern Recognition (25 คะแนน)
        bullish_patterns = 0
        bearish_patterns = 0
        
        # ตรวจสอบ Candlestick patterns ที่ปรับแล้ว
        if len(close) >= 2:
            # ใช้ open แทน close[-2] สำหรับการเปรียบเทียบที่ถูกต้อง
            open_prev = close[-2]  # ประมาณ
            open_curr = close[-1]
            
            if CandlestickPatterns.is_hammer(open_curr, high[-1], low[-1], close[-1]):
                bullish_patterns += 1
            if CandlestickPatterns.is_shooting_star(open_curr, high[-1], low[-1], close[-1]):
                bearish_patterns += 1
        
        if len(close) >= 3:
            if CandlestickPatterns.is_bullish_engulfing(close[-3], close[-2], close[-2], close[-1]):
                bullish_patterns += 1
            if CandlestickPatterns.is_bearish_engulfing(close[-3], close[-2], close[-2], close[-1]):
                bearish_patterns += 1
        
        # 2. Divergence Detection (15 คะแนน)
        divergence = AIPatternRecognition.detect_divergence(close, rsi, lookback=5)
        if divergence['bullish']:
            bullish_patterns += 1.5
        if divergence['bearish']:
            bearish_patterns += 1.5
        
        debug_info['patterns'] = {
            'bullish': bullish_patterns,
            'bearish': bearish_patterns
        }
        
        # 3. Market Regime (10 คะแนน)
        regime = AIPatternRecognition.market_regime_detection(close, 50)
        regime_score_bull = 10 if regime == 'trending' else 5 if regime == 'volatile' else 0
        regime_score_bear = 10 if regime == 'trending' else 5 if regime == 'volatile' else 0
        debug_info['regime'] = regime
        
        # 4. Momentum Quality (20 คะแนน)
        if volume is not None and len(volume) == len(close):
            momentum_quality = AIPatternRecognition.momentum_quality_index(close, high, low, volume)
            has_volume = True
        else:
            # ถ้าไม่มี volume ใช้ RSI แทน
            momentum_quality = (rsi[-1] / 100.0)  # แปลง RSI เป็น 0-1
            has_volume = False
        
        momentum_score_bull = 0
        momentum_score_bear = 0
        if momentum_quality > 0.6:
            momentum_score_bull = 20
        elif momentum_quality < 0.4:
            momentum_score_bear = 20
        else:
            # ให้คะแนนบางส่วนตาม RSI
            if rsi[-1] > 50:
                momentum_score_bull = 10
            else:
                momentum_score_bear = 10
        
        debug_info['momentum'] = {
            'quality': momentum_quality,
            'has_volume': has_volume,
            'rsi': rsi[-1]
        }
        
        # 5. Probability Models (25 คะแนน)
        short_term = UltimateAccuracyScore.calculate_short_term_probability(high, low, close, volume)
        
        prob_score_bull = 0
        prob_score_bear = 0
        if short_term['probability_up'] > 55:  # ลดเกณฑ์จาก 60 → 55
            prob_score_bull = int((short_term['probability_up'] - 50) * 5)  # 55% = 25 คะแนน
        if short_term['probability_down'] > 55:
            prob_score_bear = int((short_term['probability_down'] - 50) * 5)
        
        debug_info['probability'] = {
            'up': short_term['probability_up'],
            'down': short_term['probability_down']
        }
        
        # 6. Trend Analysis (15 คะแนน)
        hurst = TechnicalIndicators.hurst_exponent(close, min(20, len(close) - 5))
        is_trending = hurst > 0.5
        
        # Ichimoku (ปรับให้ทำงานกับข้อมูลน้อยกว่า)
        ichimoku_periods = [min(9, len(close) // 10), min(26, len(close) // 5), min(52, len(close) // 2)]
        if ichimoku_periods[2] >= 30:
            ichimoku = TechnicalIndicators.ichimoku(high, low, close, ichimoku_periods[0], ichimoku_periods[1], ichimoku_periods[2])
            cloud_top = max(ichimoku['senkou_span_a'][-1], ichimoku['senkou_span_b'][-1])
            above_cloud = close[-1] > cloud_top
        else:
            # ใช้ MA แทน
            ma_50 = TechnicalIndicators.sma(close, 50)
            above_cloud = close[-1] > ma_50[-1]
        
        trend_score_bull = 0
        trend_score_bear = 0
        if is_trending and above_cloud:
            trend_score_bull = 15
        elif is_trending and not above_cloud:
            trend_score_bear = 15
        else:
            # ไม่มีเทรนด์ชัด แต่ดู MA
            if above_cloud:
                trend_score_bull = 8
            else:
                trend_score_bear = 8
        
        debug_info['trend'] = {
            'hurst': hurst,
            'is_trending': is_trending,
            'above_cloud': above_cloud
        }
        
        # 7. ADX Trend Strength (15 คะแนน)
        adx_score_bull = 0
        adx_score_bear = 0
        if adx[-1] > 25 and di_plus[-1] > di_minus[-1]:
            adx_score_bull = 15
        elif adx[-1] > 25 and di_minus[-1] > di_plus[-1]:
            adx_score_bear = 15
        elif adx[-1] > 20:  # เพิ่มเกณฑ์ระดับกลาง
            if di_plus[-1] > di_minus[-1]:
                adx_score_bull = 8
            else:
                adx_score_bear = 8
        
        debug_info['adx'] = {
            'value': adx[-1],
            'di_plus': di_plus[-1],
            'di_minus': di_minus[-1]
        }
        
        # คำนวณคะแนนรวม
        bullish_score = (
            bullish_patterns * 10 +  # Pattern: 25 คะแนนเต็ม
            regime_score_bull +       # Regime: 10 คะแนนเต็ม
            momentum_score_bull +     # Momentum: 20 คะแนนเต็ม
            prob_score_bull +         # Probability: 25 คะแนนเต็ม
            trend_score_bull +        # Trend: 15 คะแนนเต็ม
            adx_score_bull            # ADX: 15 คะแนนเต็ม
        )
        
        bearish_score = (
            bearish_patterns * 10 +
            regime_score_bear +
            momentum_score_bear +
            prob_score_bear +
            trend_score_bear +
            adx_score_bear
        )
        
        # เก็บรายละเอียดคะแนน
        debug_info['scores'] = {
            'bullish': {
                'patterns': bullish_patterns * 10,
                'regime': regime_score_bull,
                'momentum': momentum_score_bull,
                'probability': prob_score_bull,
                'trend': trend_score_bull,
                'adx': adx_score_bull,
                'total': bullish_score
            },
            'bearish': {
                'patterns': bearish_patterns * 10,
                'regime': regime_score_bear,
                'momentum': momentum_score_bear,
                'probability': prob_score_bear,
                'trend': trend_score_bear,
                'adx': adx_score_bear,
                'total': bearish_score
            }
        }
        
        # ตัดสินใจ (ลดเกณฑ์จาก 50 → 35)
        min_score = 35
        
        # สร้าง detailed reason
        def create_reason(score_type, total_score, debug):
            details = []
            scores = debug['scores'][score_type]
            if scores['patterns'] > 0:
                details.append(f"Pattern:{scores['patterns']}")
            if scores['probability'] > 0:
                details.append(f"Prob:{scores['probability']}")
            if scores['momentum'] > 0:
                details.append(f"Mom:{scores['momentum']}")
            if scores['trend'] > 0:
                details.append(f"Trend:{scores['trend']}")
            if scores['adx'] > 0:
                details.append(f"ADX:{scores['adx']}")
            
            detail_str = ", ".join(details) if details else "ไม่มีคะแนน"
            return f"AI Multi-Factor {score_type.upper()} | Score: {total_score}/110 ({detail_str}) | Regime: {debug['regime']}"
        
        if bullish_score >= min_score and bullish_score > bearish_score:
            return {
                'signal': SignalType.BUY,
                'entry_price': curr_close,
                'stop_loss': curr_close - (atr_multiplier * curr_atr),
                'take_profit': curr_close + (atr_multiplier * curr_atr * 2.5),
                'atr': curr_atr,
                'reason': create_reason('bullish', bullish_score, debug_info),
                'debug': debug_info
            }
        
        elif bearish_score >= min_score and bearish_score > bullish_score:
            return {
                'signal': SignalType.SELL,
                'entry_price': curr_close,
                'stop_loss': curr_close + (atr_multiplier * curr_atr),
                'take_profit': curr_close - (atr_multiplier * curr_atr * 2.5),
                'atr': curr_atr,
                'reason': create_reason('bearish', bearish_score, debug_info),
                'debug': debug_info
            }
        
        # NO_TRADE - แสดงรายละเอียดว่าทำไมไม่ผ่าน
        max_score = max(bullish_score, bearish_score)
        score_type = 'Bull' if bullish_score > bearish_score else 'Bear'
        
        reason_parts = [
            f"AI Multi-Factor: คะแนนไม่เพียงพอ ({score_type}: {max_score}/110, ต้องการ {min_score}+)"
        ]
        
        # แสดงปัญหาที่เป็นไปได้
        issues = []
        if debug_info['scores']['bullish']['patterns'] == 0 and debug_info['scores']['bearish']['patterns'] == 0:
            issues.append("ไม่พบ Pattern")
        if debug_info['scores']['bullish']['probability'] < 15 and debug_info['scores']['bearish']['probability'] < 15:
            issues.append(f"Probability ต่ำ ({debug_info['probability']['up']:.0f}%/{debug_info['probability']['down']:.0f}%)")
        if not debug_info['momentum']['has_volume']:
            issues.append("ไม่มี Volume data")
        if debug_info['adx']['value'] < 20:
            issues.append(f"ADX อ่อนแอ ({debug_info['adx']['value']:.1f})")
        
        if issues:
            reason_parts.append("| ปัญหา: " + ", ".join(issues))
        
        return {
            'signal': SignalType.NO_TRADE,
            'reason': " ".join(reason_parts),
            'debug': debug_info
        }

