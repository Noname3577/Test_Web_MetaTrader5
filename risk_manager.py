"""
Risk Manager - ระบบจัดการความเสี่ยง
ตรวจสอบและควบคุมความเสี่ยงก่อนส่งคำสั่งซื้อขาย
"""

from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from config import TradingConfig
from signal_engine import TradingSignal, SignalType


@dataclass
class TradeStats:
    """สถิติการเทรดประจำวัน/สัปดาห์"""
    date: datetime
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit: float = 0.0
    total_loss: float = 0.0
    symbols_traded: Dict[str, int] = None  # {symbol: count}
    
    def __post_init__(self):
        if self.symbols_traded is None:
            self.symbols_traded = {}
    
    @property
    def net_profit(self) -> float:
        """กำไรสุทธิ"""
        return self.total_profit + self.total_loss  # loss เป็นลบอยู่แล้ว
    
    @property
    def win_rate(self) -> float:
        """เปอร์เซ็นต์ชนะ"""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100


class RiskManager:
    """
    ตัวจัดการความเสี่ยง - ตรวจสอบกฎต่างๆ ก่อนส่งคำสั่ง
    """
    
    def __init__(self):
        self.daily_stats: Dict[str, TradeStats] = {}  # {date_str: TradeStats}
        self.weekly_stats: Dict[str, TradeStats] = {}  # {week_str: TradeStats}
        self.active_positions: Dict[str, list] = {}  # {symbol: [positions]}
        self.kill_switch_active = False
        self.kill_switch_reason = ""
    
    def check_signal(self, signal: TradingSignal, account_equity: float,
                    current_positions: Dict, market_info: Dict) -> Tuple[bool, str, float]:
        """
        ตรวจสอบสัญญาณว่าผ่านกฎความเสี่ยงหรือไม่
        
        Args:
            signal: สัญญาณจาก Signal Engine
            account_equity: ทุนในบัญชี
            current_positions: positions ปัจจุบัน {symbol: count}
            market_info: ข้อมูลตลาด {'spread': float, 'ask': float, 'bid': float}
            
        Returns:
            (อนุมัติ: bool, เหตุผล: str, ขนาด lot: float)
        """
        
        # 1. ตรวจสอบ Kill Switch
        if self.kill_switch_active:
            return False, f"Kill Switch ถูกเปิดใช้งาน: {self.kill_switch_reason}", 0.0
        
        # 2. ตรวจสอบประเภทสัญญาณ
        if signal.signal == SignalType.NO_TRADE:
            return False, "ไม่มีสัญญาณเทรด", 0.0
        
        # 3. ตรวจสอบจำนวน position ต่อสัญลักษณ์
        symbol_positions = current_positions.get(signal.symbol, 0)
        if symbol_positions >= TradingConfig.MAX_POSITIONS_PER_SYMBOL:
            return False, f"มี position เต็มแล้วสำหรับ {signal.symbol} ({symbol_positions}/{TradingConfig.MAX_POSITIONS_PER_SYMBOL})", 0.0
        
        # 4. ตรวจสอบจำนวนไม้ต่อวัน
        today = datetime.now().strftime("%Y-%m-%d")
        daily_stat = self.daily_stats.get(today, TradeStats(datetime.now()))
        
        if daily_stat.total_trades >= TradingConfig.MAX_TRADES_PER_DAY:
            return False, f"ถึงจำนวนไม้สูงสุดต่อวันแล้ว ({daily_stat.total_trades}/{TradingConfig.MAX_TRADES_PER_DAY})", 0.0
        
        # 5. ตรวจสอบจำนวนไม้ต่อสัญลักษณ์ต่อวัน
        symbol_trades_today = daily_stat.symbols_traded.get(signal.symbol, 0)
        if symbol_trades_today >= TradingConfig.MAX_TRADES_PER_SYMBOL_PER_DAY:
            return False, f"ถึงจำนวนไม้สูงสุดต่อวันสำหรับ {signal.symbol} ({symbol_trades_today}/{TradingConfig.MAX_TRADES_PER_SYMBOL_PER_DAY})", 0.0
        
        # 6. ตรวจสอบ Spread
        spread = market_info.get('spread', 0)
        if spread > TradingConfig.MAX_SPREAD_POINTS:
            return False, f"Spread สูงเกินไป ({spread:.1f} > {TradingConfig.MAX_SPREAD_POINTS})", 0.0
        
        # 7. ตรวจสอบขาดทุนสะสม (Daily Loss Limit)
        daily_loss_limit = account_equity * (TradingConfig.DAILY_LOSS_LIMIT_PERCENT / 100)
        if abs(daily_stat.total_loss) >= daily_loss_limit:
            self._activate_kill_switch(f"ขาดทุนเกิน Daily Limit ({abs(daily_stat.total_loss):.2f} >= {daily_loss_limit:.2f})")
            return False, self.kill_switch_reason, 0.0
        
        # 8. ตรวจสอบขาดทุนสะสม (Weekly Loss Limit)
        week_key = datetime.now().strftime("%Y-W%W")
        weekly_stat = self.weekly_stats.get(week_key, TradeStats(datetime.now()))
        weekly_loss_limit = account_equity * (TradingConfig.WEEKLY_LOSS_LIMIT_PERCENT / 100)
        
        if abs(weekly_stat.total_loss) >= weekly_loss_limit:
            self._activate_kill_switch(f"ขาดทุนเกิน Weekly Limit ({abs(weekly_stat.total_loss):.2f} >= {weekly_loss_limit:.2f})")
            return False, self.kill_switch_reason, 0.0
        
        # 9. ตรวจสอบช่วงเวลาเทรด
        current_hour = datetime.now().hour
        if not (TradingConfig.TRADING_START_HOUR <= current_hour <= TradingConfig.TRADING_END_HOUR):
            return False, f"อยู่นอกช่วงเวลาเทรด ({TradingConfig.TRADING_START_HOUR}-{TradingConfig.TRADING_END_HOUR} UTC)", 0.0
        
        # 10. คำนวณขนาด lot
        lot_size = self.calculate_position_size(
            account_equity, signal.risk_points, market_info
        )
        
        if lot_size <= 0:
            return False, "ไม่สามารถคำนวณขนาด lot ได้", 0.0
        
        # ผ่านทุกเงื่อนไข
        return True, "ผ่านการตรวจสอบความเสี่ยงทั้งหมด", lot_size
    
    def calculate_position_size(self, equity: float, stop_distance: float,
                               market_info: Dict) -> float:
        """
        คำนวณขนาด lot ตามความเสี่ยงที่กำหนด
        
        สูตร:
        RiskMoney = Equity × RiskPercent
        PositionSize = RiskMoney / (StopDistance × ValuePerPoint)
        
        Args:
            equity: ทุนในบัญชี
            stop_distance: ระยะ stop loss (ในหน่วยราคา)
            market_info: {'point': float, 'tick_value': float, 'volume_min': float, 'volume_step': float}
            
        Returns:
            ขนาด lot ที่คำนวณได้
        """
        try:
            # เงินที่เสี่ยงต่อไม้
            risk_money = equity * (TradingConfig.RISK_PER_TRADE_PERCENT / 100)
            
            # ดึงข้อมูลจากตลาด
            point = market_info.get('point', 0.00001)  # ค่า point (เช่น 0.00001 สำหรับ EURUSD)
            tick_value = market_info.get('tick_value', 1.0)  # มูลค่าต่อ tick
            volume_min = market_info.get('volume_min', 0.01)  # lot ขั้นต่ำ
            volume_step = market_info.get('volume_step', 0.01)  # ขั้นของ lot
            
            # คำนวณ lot
            stop_distance_points = stop_distance / point  # แปลงเป็น points
            lot_size = risk_money / (stop_distance_points * tick_value)
            
            # ปรับให้ตรงกับ volume_step
            lot_size = max(volume_min, lot_size)
            lot_size = round(lot_size / volume_step) * volume_step
            
            return lot_size
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการคำนวณ lot: {e}")
            return 0.0
    
    def record_trade(self, symbol: str, profit_loss: float):
        """
        บันทึกผลการเทรด
        
        Args:
            symbol: ชื่อสัญลักษณ์
            profit_loss: กำไร/ขาดทุน (+ = กำไร, - = ขาดทุน)
        """
        today = datetime.now().strftime("%Y-%m-%d")
        week_key = datetime.now().strftime("%Y-W%W")
        
        # อัปเดต daily stats
        if today not in self.daily_stats:
            self.daily_stats[today] = TradeStats(datetime.now())
        
        daily_stat = self.daily_stats[today]
        daily_stat.total_trades += 1
        
        if profit_loss > 0:
            daily_stat.winning_trades += 1
            daily_stat.total_profit += profit_loss
        else:
            daily_stat.losing_trades += 1
            daily_stat.total_loss += profit_loss
        
        # นับจำนวนไม้ต่อสัญลักษณ์
        daily_stat.symbols_traded[symbol] = daily_stat.symbols_traded.get(symbol, 0) + 1
        
        # อัปเดต weekly stats
        if week_key not in self.weekly_stats:
            self.weekly_stats[week_key] = TradeStats(datetime.now())
        
        weekly_stat = self.weekly_stats[week_key]
        weekly_stat.total_trades += 1
        
        if profit_loss > 0:
            weekly_stat.winning_trades += 1
            weekly_stat.total_profit += profit_loss
        else:
            weekly_stat.losing_trades += 1
            weekly_stat.total_loss += profit_loss
        
        weekly_stat.symbols_traded[symbol] = weekly_stat.symbols_traded.get(symbol, 0) + 1
    
    def _activate_kill_switch(self, reason: str):
        """เปิดใช้งาน Kill Switch"""
        self.kill_switch_active = True
        self.kill_switch_reason = reason
        print(f"\n⚠️ KILL SWITCH ACTIVATED: {reason}\n")
    
    def deactivate_kill_switch(self):
        """ปิดใช้งาน Kill Switch (ต้องทำด้วยมือ)"""
        self.kill_switch_active = False
        self.kill_switch_reason = ""
        print("✅ Kill Switch ถูกปิดใช้งานแล้ว")
    
    def get_daily_report(self, date: Optional[str] = None) -> Dict:
        """
        ดึงรายงานประจำวัน
        
        Args:
            date: วันที่ในรูปแบบ "YYYY-MM-DD" (None = วันนี้)
            
        Returns:
            dict ของสถิติ
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        stat = self.daily_stats.get(date, TradeStats(datetime.now()))
        
        return {
            'date': date,
            'total_trades': stat.total_trades,
            'winning_trades': stat.winning_trades,
            'losing_trades': stat.losing_trades,
            'win_rate': round(stat.win_rate, 2),
            'total_profit': round(stat.total_profit, 2),
            'total_loss': round(stat.total_loss, 2),
            'net_profit': round(stat.net_profit, 2),
            'symbols_traded': stat.symbols_traded
        }
    
    def get_weekly_report(self, week_key: Optional[str] = None) -> Dict:
        """
        ดึงรายงานประจำสัปดาห์
        
        Args:
            week_key: สัปดาห์ในรูปแบบ "YYYY-WXX" (None = สัปดาห์นี้)
            
        Returns:
            dict ของสถิติ
        """
        if week_key is None:
            week_key = datetime.now().strftime("%Y-W%W")
        
        stat = self.weekly_stats.get(week_key, TradeStats(datetime.now()))
        
        return {
            'week': week_key,
            'total_trades': stat.total_trades,
            'winning_trades': stat.winning_trades,
            'losing_trades': stat.losing_trades,
            'win_rate': round(stat.win_rate, 2),
            'total_profit': round(stat.total_profit, 2),
            'total_loss': round(stat.total_loss, 2),
            'net_profit': round(stat.net_profit, 2),
            'symbols_traded': stat.symbols_traded
        }
    
    def check_max_slippage(self, expected_price: float, executed_price: float,
                          point: float) -> Tuple[bool, float]:
        """
        ตรวจสอบ slippage หลังส่งคำสั่ง
        
        Args:
            expected_price: ราคาที่คาดหวัง
            executed_price: ราคาที่ได้จริง
            point: ขนาดของ 1 point
            
        Returns:
            (ยอมรับได้: bool, slippage_points: float)
        """
        slippage = abs(expected_price - executed_price) / point
        acceptable = slippage <= TradingConfig.MAX_SLIPPAGE_POINTS
        
        return acceptable, slippage


# ตัวอย่างการใช้งาน
if __name__ == "__main__":
    risk_mgr = RiskManager()
    
    # ทดสอบคำนวณ lot size
    equity = 10000  # $10,000
    stop_distance = 0.0050  # 50 pips
    market_info = {
        'point': 0.00001,
        'tick_value': 1.0,
        'volume_min': 0.01,
        'volume_step': 0.01
    }
    
    lot_size = risk_mgr.calculate_position_size(equity, stop_distance, market_info)
    print(f"ขนาด lot ที่คำนวณได้: {lot_size:.2f}")
    print(f"เสี่ยง: ${equity * 0.01:.2f} ({TradingConfig.RISK_PER_TRADE_PERCENT}% ของ equity)")
    
    # ทดสอบบันทึกผลการเทรด
    risk_mgr.record_trade("EURUSD", 150.0)  # ชนะ $150
    risk_mgr.record_trade("GBPUSD", -100.0)  # แพ้ $100
    risk_mgr.record_trade("EURUSD", 200.0)  # ชนะ $200
    
    # แสดงรายงาน
    print("\n=== รายงานประจำวัน ===")
    daily = risk_mgr.get_daily_report()
    for key, value in daily.items():
        print(f"{key}: {value}")
