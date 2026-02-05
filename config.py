"""
Configuration Module
การตั้งค่าสำหรับ Trading Bot
"""

from enum import Enum
from typing import Dict, Any


class ExecutionMode(Enum):
    """โหมดการทำงานของระบบ"""
    DRY_RUN = "dry_run"  # คำนวณ+บันทึก+แจ้งเตือน แต่ไม่ส่งออเดอร์
    MANUAL_CONFIRM = "manual_confirm"  # รอคนยืนยันก่อนส่งคำสั่ง
    AUTO = "auto"  # ส่งออเดอร์อัตโนมัติ


class StrategyType(Enum):
    """ประเภทกลยุทธ์การเทรด"""
    MA_CROSSOVER = "ma_crossover"
    DONCHIAN_BREAKOUT = "donchian_breakout"
    BOLLINGER_BANDS = "bollinger_bands"
    RSI_SWING = "rsi_swing"
    MACD = "macd"
    ATR_TRAILING = "atr_trailing"
    SUPERTREND = "supertrend"


class TradingConfig:
    """การตั้งค่าหลักสำหรับระบบเทรด"""
    
    # โหมดการทำงาน
    EXECUTION_MODE = ExecutionMode.DRY_RUN
    
    # การจัดการความเสี่ยง
    RISK_PER_TRADE_PERCENT = 1.0  # % ของ equity ที่เสี่ยงต่อไม้
    MAX_POSITIONS_PER_SYMBOL = 1  # จำนวน position สูงสุดต่อสัญลักษณ์
    MAX_TRADES_PER_DAY = 3  # จำนวนไม้สูงสุดต่อวัน (ทุกสัญลักษณ์รวม)
    MAX_TRADES_PER_SYMBOL_PER_DAY = 1  # จำนวนไม้สูงสุดต่อสัญลักษณ์ต่อวัน
    
    # การควบคุมการเทรด
    MAX_SLIPPAGE_POINTS = 5  # slippage สูงสุดที่ยอมรับได้ (points)
    MAX_SPREAD_POINTS = 10  # spread สูงสุดที่ยอมรับได้ (points)
    
    # Kill Switch - หยุดระบบเมื่อขาดทุนเกินกำหนด
    DAILY_LOSS_LIMIT_PERCENT = 3.0  # % ของ equity
    WEEKLY_LOSS_LIMIT_PERCENT = 5.0  # % ของ equity
    
    # ช่วงเวลาเทรด (UTC)
    TRADING_START_HOUR = 0  # เริ่มเทรดเวลา 00:00 UTC
    TRADING_END_HOUR = 23  # หยุดเทรดเวลา 23:00 UTC
    
    # ข่าวเศรษฐกิจ (ถ้ามีปฏิทินข่าว)
    AVOID_NEWS_TRADING = True  # หลีกเลี่ยงเทรดช่วงข่าวแรง
    NEWS_BUFFER_MINUTES = 30  # หยุดเทรดก่อนข่าว 30 นาที
    
    # Timeframe สำหรับวิเคราะห์
    DEFAULT_TIMEFRAME = "D1"  # Daily chart


class StrategyConfigs:
    """พารามิเตอร์สำหรับแต่ละกลยุทธ์"""
    
    MA_CROSSOVER = {
        "fast_period": 10,
        "slow_period": 30,
        "ma_type": "EMA",  # "EMA" หรือ "SMA"
        "atr_period": 14,
        "atr_multiplier": 2.0,  # สำหรับกำหนด stop loss
        "risk_reward_ratio": 2.0  # TP = SL × 2
    }
    
    DONCHIAN_BREAKOUT = {
        "entry_period": 20,  # ดูจุดสูง/ต่ำ 20 วัน
        "exit_period": 10,  # ดูจุดสูง/ต่ำ 10 วัน
        "atr_period": 14,
        "atr_multiplier": 2.0,
        "risk_reward_ratio": 3.0
    }
    
    BOLLINGER_BANDS = {
        "period": 20,
        "std_dev": 2.0,  # จำนวน standard deviation
        "rsi_period": 14,
        "rsi_oversold": 30,  # RSI < 30 ถือว่า oversold
        "rsi_overbought": 70,  # RSI > 70 ถือว่า overbought
        "atr_period": 14,
        "atr_multiplier": 1.5,
        "risk_reward_ratio": 2.0
    }
    
    RSI_SWING = {
        "rsi_period": 14,
        "oversold_level": 30,
        "overbought_level": 70,
        "exit_level": 50,  # ออกเมื่อ RSI กลับไปที่ 50
        "atr_period": 14,
        "atr_multiplier": 2.0,
        "risk_reward_ratio": 2.5
    }
    
    MACD = {
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9,
        "atr_period": 14,
        "atr_multiplier": 2.0,
        "risk_reward_ratio": 2.0
    }
    
    ATR_TRAILING = {
        "atr_period": 14,
        "atr_multiplier": 3.0,  # ระยะห่างของ trailing stop
        "trend_ma_period": 50,  # ใช้ MA เป็นตัวกรองเทรนด์
        "risk_reward_ratio": 3.0
    }
    
    SUPERTREND = {
        "atr_period": 10,
        "atr_multiplier": 3.0,
        "risk_reward_ratio": 2.5
    }


class LogConfig:
    """การตั้งค่าการบันทึก log"""
    
    LOG_TRADES = True  # บันทึกการเทรดทั้งหมด
    LOG_SIGNALS = True  # บันทึกสัญญาณทั้งหมด (รวม NO_TRADE)
    LOG_RISK_CHECKS = True  # บันทึกการตรวจสอบความเสี่ยง
    LOG_ERRORS = True  # บันทึก error
    
    LOG_DIR = "logs"  # โฟลเดอร์สำหรับเก็บ log
    TRADE_LOG_FILE = "trades.log"
    SIGNAL_LOG_FILE = "signals.log"
    ERROR_LOG_FILE = "errors.log"


# ฟังก์ชันช่วยเหลือ
def get_strategy_config(strategy_type: StrategyType) -> Dict[str, Any]:
    """ดึงพารามิเตอร์ของกลยุทธ์ตามประเภท"""
    config_map = {
        StrategyType.MA_CROSSOVER: StrategyConfigs.MA_CROSSOVER,
        StrategyType.DONCHIAN_BREAKOUT: StrategyConfigs.DONCHIAN_BREAKOUT,
        StrategyType.BOLLINGER_BANDS: StrategyConfigs.BOLLINGER_BANDS,
        StrategyType.RSI_SWING: StrategyConfigs.RSI_SWING,
        StrategyType.MACD: StrategyConfigs.MACD,
        StrategyType.ATR_TRAILING: StrategyConfigs.ATR_TRAILING,
        StrategyType.SUPERTREND: StrategyConfigs.SUPERTREND
    }
    return config_map.get(strategy_type, {})


def set_execution_mode(mode: ExecutionMode):
    """เปลี่ยนโหมดการทำงาน"""
    TradingConfig.EXECUTION_MODE = mode


def get_execution_mode() -> ExecutionMode:
    """ดึงโหมดการทำงานปัจจุบัน"""
    return TradingConfig.EXECUTION_MODE
