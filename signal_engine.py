"""
Signal Engine - เครื่องมือสร้างสัญญาณการเทรด
อ่านข้อมูล → คำนวณ → ออก "คำแนะนำ" (BUY/SELL/NO_TRADE, SL/TP, risk)
"""

import numpy as np
from typing import Dict, Optional
from datetime import datetime
from config import StrategyType, get_strategy_config
from strategies import (
    SignalType, Strategy1_MACrossover, Strategy2_DonchianBreakout,
    Strategy3_BollingerBands, Strategy4_RSISwing, Strategy5_MACD,
    Strategy6_ATRTrailing, Strategy7_Supertrend, Strategy8_UltimateAccuracy,
    Strategy9_AIMultiFactor
)


class TradingSignal:
    """คลาสสำหรับเก็บข้อมูลสัญญาณการเทรด"""
    
    def __init__(self, symbol: str, strategy: StrategyType, signal_data: Dict):
        self.symbol = symbol
        self.strategy = strategy
        self.timestamp = datetime.now()
        
        # ข้อมูลสัญญาณ
        self.signal = signal_data.get('signal', SignalType.NO_TRADE)
        self.entry_price = signal_data.get('entry_price', 0.0)
        self.stop_loss = signal_data.get('stop_loss', 0.0)
        self.take_profit = signal_data.get('take_profit', 0.0)
        self.atr = signal_data.get('atr', 0.0)
        self.reason = signal_data.get('reason', '')
        
        # คำนวณความเสี่ยง
        self.risk_points = abs(self.entry_price - self.stop_loss) if self.entry_price > 0 else 0
        self.reward_points = abs(self.take_profit - self.entry_price) if self.entry_price > 0 else 0
        self.risk_reward_ratio = self.reward_points / self.risk_points if self.risk_points > 0 else 0
    
    def to_dict(self) -> Dict:
        """แปลงเป็น dictionary"""
        return {
            'symbol': self.symbol,
            'strategy': self.strategy.value,
            'timestamp': self.timestamp.isoformat(),
            'signal': self.signal.value if isinstance(self.signal, SignalType) else str(self.signal),
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'atr': self.atr,
            'risk_points': self.risk_points,
            'reward_points': self.reward_points,
            'risk_reward_ratio': round(self.risk_reward_ratio, 2),
            'reason': self.reason
        }
    
    def __str__(self) -> str:
        """แสดงข้อมูลแบบอ่านง่าย"""
        signal_value = self.signal.value if isinstance(self.signal, SignalType) else str(self.signal)
        
        if signal_value == "NO_TRADE":
            return f"[{self.symbol}] {self.strategy.value}: NO_TRADE - {self.reason}"
        
        return (
            f"[{self.symbol}] {self.strategy.value}: {signal_value}\n"
            f"  Entry: {self.entry_price:.5f}\n"
            f"  SL: {self.stop_loss:.5f} (Risk: {self.risk_points:.5f})\n"
            f"  TP: {self.take_profit:.5f} (Reward: {self.reward_points:.5f})\n"
            f"  RR: 1:{self.risk_reward_ratio:.2f}\n"
            f"  ATR: {self.atr:.5f}\n"
            f"  Reason: {self.reason}"
        )


class SignalEngine:
    """
    เครื่องมือสร้างสัญญาณ - ส่วนที่ 1 ของระบบ
    หน้าที่: วิเคราะห์ข้อมูล → คำนวณตามกลยุทธ์ → ออกคำแนะนำ
    """
    
    def __init__(self):
        self.strategy_map = {
            StrategyType.MA_CROSSOVER: Strategy1_MACrossover,
            StrategyType.DONCHIAN_BREAKOUT: Strategy2_DonchianBreakout,
            StrategyType.BOLLINGER_BANDS: Strategy3_BollingerBands,
            StrategyType.RSI_SWING: Strategy4_RSISwing,
            StrategyType.MACD: Strategy5_MACD,
            StrategyType.ATR_TRAILING: Strategy6_ATRTrailing,
            StrategyType.SUPERTREND: Strategy7_Supertrend,
            StrategyType.ULTIMATE_ACCURACY: Strategy8_UltimateAccuracy,
            StrategyType.AI_MULTI_FACTOR: Strategy9_AIMultiFactor
        }
    
    def generate_signal(self, symbol: str, strategy_type: StrategyType,
                       high: np.ndarray, low: np.ndarray, close: np.ndarray) -> TradingSignal:
        """
        สร้างสัญญาณจากข้อมูลราคา
        
        Args:
            symbol: ชื่อสัญลักษณ์ เช่น "EURUSD"
            strategy_type: ประเภทกลยุทธ์
            high: array ของราคาสูงสุด
            low: array ของราคาต่ำสุด
            close: array ของราคาปิด
            
        Returns:
            TradingSignal object พร้อมคำแนะนำ
        """
        try:
            # ดึงพารามิเตอร์ของกลยุทธ์
            config = get_strategy_config(strategy_type)
            
            # เลือก Strategy class
            strategy_class = self.strategy_map.get(strategy_type)
            if not strategy_class:
                return TradingSignal(symbol, strategy_type, {
                    'signal': SignalType.NO_TRADE,
                    'reason': 'ไม่พบกลยุทธ์ที่เลือก'
                })
            
            # เรียกใช้งานกลยุทธ์
            signal_data = self._execute_strategy(
                strategy_class, strategy_type, high, low, close, config
            )
            
            # สร้าง TradingSignal object
            return TradingSignal(symbol, strategy_type, signal_data)
            
        except Exception as e:
            return TradingSignal(symbol, strategy_type, {
                'signal': SignalType.NO_TRADE,
                'reason': f'เกิดข้อผิดพลาด: {str(e)}'
            })
    
    def _execute_strategy(self, strategy_class, strategy_type: StrategyType,
                         high: np.ndarray, low: np.ndarray, close: np.ndarray,
                         config: Dict) -> Dict:
        """เรียกใช้งานกลยุทธ์ตามประเภท"""
        
        if strategy_type == StrategyType.MA_CROSSOVER:
            return strategy_class.generate_signal(
                high, low, close,
                fast_period=config.get('fast_period', 10),
                slow_period=config.get('slow_period', 30),
                atr_period=config.get('atr_period', 14),
                atr_multiplier=config.get('atr_multiplier', 2.0)
            )
        
        elif strategy_type == StrategyType.DONCHIAN_BREAKOUT:
            return strategy_class.generate_signal(
                high, low, close,
                entry_period=config.get('entry_period', 20),
                exit_period=config.get('exit_period', 10),
                atr_period=config.get('atr_period', 14),
                atr_multiplier=config.get('atr_multiplier', 2.0)
            )
        
        elif strategy_type == StrategyType.BOLLINGER_BANDS:
            return strategy_class.generate_signal(
                high, low, close,
                bb_period=config.get('period', 20),
                std_dev=config.get('std_dev', 2.0),
                rsi_period=config.get('rsi_period', 14),
                rsi_oversold=config.get('rsi_oversold', 30),
                rsi_overbought=config.get('rsi_overbought', 70),
                atr_period=config.get('atr_period', 14),
                atr_multiplier=config.get('atr_multiplier', 1.5)
            )
        
        elif strategy_type == StrategyType.RSI_SWING:
            return strategy_class.generate_signal(
                high, low, close,
                rsi_period=config.get('rsi_period', 14),
                oversold=config.get('oversold_level', 30),
                overbought=config.get('overbought_level', 70),
                exit_level=config.get('exit_level', 50),
                atr_period=config.get('atr_period', 14),
                atr_multiplier=config.get('atr_multiplier', 2.0)
            )
        
        elif strategy_type == StrategyType.MACD:
            return strategy_class.generate_signal(
                high, low, close,
                fast=config.get('fast_period', 12),
                slow=config.get('slow_period', 26),
                signal_period=config.get('signal_period', 9),
                atr_period=config.get('atr_period', 14),
                atr_multiplier=config.get('atr_multiplier', 2.0)
            )
        
        elif strategy_type == StrategyType.ATR_TRAILING:
            return strategy_class.generate_signal(
                high, low, close,
                atr_period=config.get('atr_period', 14),
                atr_multiplier=config.get('atr_multiplier', 3.0),
                trend_ma_period=config.get('trend_ma_period', 50)
            )
        
        elif strategy_type == StrategyType.SUPERTREND:
            return strategy_class.generate_signal(
                high, low, close,
                atr_period=config.get('atr_period', 10),
                atr_multiplier=config.get('atr_multiplier', 3.0)
            )
        
        elif strategy_type == StrategyType.ULTIMATE_ACCURACY:
            return strategy_class.generate_signal(
                high, low, close,
                volume=None,
                atr_period=config.get('atr_period', 14),
                atr_multiplier=config.get('atr_multiplier', 2.0),
                min_accuracy=config.get('min_accuracy', 75.0)
            )
        
        elif strategy_type == StrategyType.AI_MULTI_FACTOR:
            return strategy_class.generate_signal(
                high, low, close,
                volume=None,
                atr_period=config.get('atr_period', 14),
                atr_multiplier=config.get('atr_multiplier', 2.0)
            )
        
        return {'signal': SignalType.NO_TRADE, 'reason': 'ไม่รองรับกลยุทธ์นี้'}
    
    def scan_multiple_symbols(self, symbols: list, strategy_type: StrategyType,
                            data_dict: Dict[str, Dict]) -> list:
        """
        สแกนหลายสัญลักษณ์พร้อมกัน
        
        Args:
            symbols: list ของชื่อสัญลักษณ์
            strategy_type: กลยุทธ์ที่ใช้
            data_dict: dict ที่เก็บข้อมูล {symbol: {'high': [], 'low': [], 'close': []}}
            
        Returns:
            list ของ TradingSignal ที่มีสัญญาณ BUY/SELL เท่านั้น
        """
        signals = []
        
        for symbol in symbols:
            if symbol not in data_dict:
                continue
            
            data = data_dict[symbol]
            high = np.array(data.get('high', []))
            low = np.array(data.get('low', []))
            close = np.array(data.get('close', []))
            
            if len(close) < 50:  # ต้องมีข้อมูลพอสมควร
                continue
            
            signal = self.generate_signal(symbol, strategy_type, high, low, close)
            
            # เก็บเฉพาะสัญญาณที่ไม่ใช่ NO_TRADE
            if signal.signal != SignalType.NO_TRADE:
                signals.append(signal)
        
        return signals


class SignalLogger:
    """คลาสสำหรับบันทึกสัญญาณ"""
    
    def __init__(self, log_file: str = "signals.log"):
        self.log_file = log_file
    
    def log_signal(self, signal: TradingSignal):
        """บันทึกสัญญาณลงไฟล์"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"{signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(str(signal))
                f.write(f"\n{'='*60}\n")
        except Exception as e:
            print(f"ไม่สามารถบันทึก log: {e}")
    
    def log_dict(self, data: Dict):
        """บันทึกข้อมูล dict ลงไฟล์"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{datetime.now().isoformat()}: {data}\n")
        except Exception as e:
            print(f"ไม่สามารถบันทึก log: {e}")


# ตัวอย่างการใช้งาน
if __name__ == "__main__":
    # ทดสอบ Signal Engine
    engine = SignalEngine()
    
    # สร้างข้อมูลทดสอบ (ควรมาจาก MT5 จริง)
    np.random.seed(42)
    n = 100
    close = np.cumsum(np.random.randn(n) * 0.001) + 1.1000
    high = close + np.random.rand(n) * 0.0010
    low = close - np.random.rand(n) * 0.0010
    
    # ทดสอบทุกกลยุทธ์
    print("=== ทดสอบ Signal Engine ===\n")
    
    for strategy in StrategyType:
        signal = engine.generate_signal("EURUSD", strategy, high, low, close)
        print(f"\n{strategy.value}:")
        print(signal)
        print()
