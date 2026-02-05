"""
Position Size Calculator
เครื่องคำนวณขนาด Position, Risk, และ Potential P/L
แสดงผลก่อนเปิดไม้เพื่อตัดสินใจ
"""

from typing import Dict, Tuple
from dataclasses import dataclass
from config import TradingConfig


@dataclass
class PositionCalculation:
    """ผลลัพธ์การคำนวณ Position"""
    symbol: str
    direction: str  # "BUY" or "SELL"
    entry_price: float
    stop_loss: float
    take_profit: float
    
    # ข้อมูลจากตลาด
    point: float
    tick_value: float
    contract_size: float
    
    # ผลการคำนวณ
    lot_size: float
    risk_amount: float
    reward_amount: float
    risk_reward_ratio: float
    
    # ระยะทาง
    stop_distance_points: float
    profit_distance_points: float
    stop_distance_pips: float
    profit_distance_pips: float
    
    # Account Info
    account_equity: float
    risk_percent: float
    
    @property
    def risk_reward_text(self) -> str:
        """แสดง Risk:Reward เป็นข้อความ"""
        return f"1:{self.risk_reward_ratio:.2f}"
    
    @property
    def is_valid(self) -> bool:
        """เช็คว่าการคำนวณถูกต้องหรือไม่"""
        return self.lot_size > 0 and self.risk_reward_ratio > 0


class PositionCalculator:
    """
    เครื่องคำนวณขนาด Position และ Risk/Reward
    ช่วยในการตัดสินใจก่อนเปิดไม้
    """
    
    @staticmethod
    def calculate(
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        account_equity: float,
        market_info: Dict,
        risk_percent: float = None
    ) -> PositionCalculation:
        """
        คำนวณข้อมูล Position แบบละเอียด
        
        Args:
            symbol: สัญลักษณ์ เช่น "EURUSD"
            direction: "BUY" หรือ "SELL"
            entry_price: ราคาเข้า
            stop_loss: ราคา Stop Loss
            take_profit: ราคา Take Profit
            account_equity: ทุนในบัญชี
            market_info: {'point': float, 'tick_value': float, 'contract_size': float,
                         'volume_min': float, 'volume_step': float}
            risk_percent: % ของทุนที่เสี่ยง (ถ้าไม่ระบุจะใช้จาก config)
        
        Returns:
            PositionCalculation object
        """
        if risk_percent is None:
            risk_percent = TradingConfig.RISK_PER_TRADE_PERCENT
        
        # ดึงข้อมูลจากตลาด
        point = market_info.get('point', 0.00001)
        tick_value = market_info.get('tick_value', 1.0)
        contract_size = market_info.get('contract_size', 100000)
        volume_min = market_info.get('volume_min', 0.01)
        volume_step = market_info.get('volume_step', 0.01)
        
        # คำนวณระยะทาง Stop Loss (ในหน่วย price)
        if direction == "BUY":
            stop_distance = entry_price - stop_loss
            profit_distance = take_profit - entry_price
        else:  # SELL
            stop_distance = stop_loss - entry_price
            profit_distance = entry_price - take_profit
        
        # แปลงเป็น points และ pips
        stop_distance_points = stop_distance / point
        profit_distance_points = profit_distance / point
        
        # Pips (สำหรับ pairs ที่มี JPY ให้หาร 100, อื่นๆ หาร 10)
        if "JPY" in symbol:
            pip_factor = 100
        else:
            pip_factor = 10
        
        stop_distance_pips = stop_distance_points / pip_factor
        profit_distance_pips = profit_distance_points / pip_factor
        
        # คำนวณเงินที่เสี่ยง
        risk_amount = account_equity * (risk_percent / 100)
        
        # คำนวณ Lot Size
        # Risk = Lot × Stop Distance × Tick Value
        # Lot = Risk / (Stop Distance × Tick Value)
        
        value_per_point = tick_value / point
        lot_size = risk_amount / (stop_distance * value_per_point)
        
        # ปรับให้ตรงกับ volume_min และ volume_step
        lot_size = max(lot_size, volume_min)
        lot_size = round(lot_size / volume_step) * volume_step
        
        # คำนวณ Reward
        reward_amount = lot_size * profit_distance * value_per_point
        
        # Risk:Reward Ratio
        risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
        
        return PositionCalculation(
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            point=point,
            tick_value=tick_value,
            contract_size=contract_size,
            lot_size=lot_size,
            risk_amount=risk_amount,
            reward_amount=reward_amount,
            risk_reward_ratio=risk_reward_ratio,
            stop_distance_points=stop_distance_points,
            profit_distance_points=profit_distance_points,
            stop_distance_pips=stop_distance_pips,
            profit_distance_pips=profit_distance_pips,
            account_equity=account_equity,
            risk_percent=risk_percent
        )
    
    @staticmethod
    def calculate_from_signal(signal, account_equity: float, market_info: Dict) -> PositionCalculation:
        """
        คำนวณจาก TradingSignal object
        
        Args:
            signal: TradingSignal object
            account_equity: ทุนในบัญชี
            market_info: ข้อมูลตลาด
        
        Returns:
            PositionCalculation object
        """
        direction = signal.signal.value  # "BUY" or "SELL"
        
        return PositionCalculator.calculate(
            symbol=signal.symbol,
            direction=direction,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            account_equity=account_equity,
            market_info=market_info
        )
    
    @staticmethod
    def format_calculation(calc: PositionCalculation) -> str:
        """
        จัดรูปแบบผลการคำนวณเป็น text
        
        Args:
            calc: PositionCalculation object
        
        Returns:
            ข้อความแสดงผล
        """
        status_icon = "✅" if calc.is_valid else "❌"
        direction_icon = "🟢" if calc.direction == "BUY" else "🔴"
        
        text = f"""
{status_icon} POSITION CALCULATION {status_icon}
{'═'*50}

{direction_icon} {calc.direction} {calc.symbol}
{'─'*50}

📊 ENTRY DETAILS
  Entry Price:        {calc.entry_price:.5f}
  Stop Loss:          {calc.stop_loss:.5f}
  Take Profit:        {calc.take_profit:.5f}

💼 POSITION SIZE
  Lot Size:           {calc.lot_size:.2f} lots
  Contract Size:      {calc.contract_size:,.0f}

📏 DISTANCE
  SL Distance:        {calc.stop_distance_pips:.1f} pips ({calc.stop_distance_points:.1f} points)
  TP Distance:        {calc.profit_distance_pips:.1f} pips ({calc.profit_distance_points:.1f} points)

💰 RISK & REWARD
  Risk Amount:        ${calc.risk_amount:,.2f} ({calc.risk_percent:.1f}% of Equity)
  Reward Amount:      ${calc.reward_amount:,.2f}
  Risk:Reward:        {calc.risk_reward_text}

💼 ACCOUNT INFO
  Current Equity:     ${calc.account_equity:,.2f}
  
⚡ POTENTIAL P/L
  If Hit SL:          -${calc.risk_amount:,.2f} ({-calc.risk_percent:.1f}%)
  If Hit TP:          +${calc.reward_amount:,.2f} ({calc.reward_amount/calc.account_equity*100:.1f}%)

{'═'*50}
"""
        return text
    
    @staticmethod
    def quick_summary(calc: PositionCalculation) -> str:
        """สรุปแบบย่อ (สำหรับแสดงใน GUI)"""
        return f"""
{calc.direction} {calc.symbol} | Lot: {calc.lot_size:.2f}
Risk: ${calc.risk_amount:.2f} | Reward: ${calc.reward_amount:.2f}
R:R = {calc.risk_reward_text} | SL: {calc.stop_distance_pips:.1f} pips | TP: {calc.profit_distance_pips:.1f} pips
"""
