"""
Execution Engine - เครื่องมือส่งคำสั่งซื้อขาย
รับคำแนะนำ → ตรวจ risk & เงื่อนไข → ส่งออเดอร์/หรือรอคนยืนยัน
"""

from typing import Dict, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime
from config import ExecutionMode, get_execution_mode, TradingConfig
from signal_engine import TradingSignal, SignalType
from risk_manager import RiskManager
from mt5_handler import MT5Handler


@dataclass
class TradeTicket:
    """ตั๋วคำสั่งซื้อขาย - ใช้สำหรับโหมด MANUAL_CONFIRM"""
    id: str
    signal: TradingSignal
    lot_size: float
    approved: bool = False
    executed: bool = False
    ticket_number: Optional[int] = None
    execution_time: Optional[datetime] = None
    execution_price: Optional[float] = None
    result_message: str = ""
    
    def __str__(self):
        status = "รอยืนยัน"
        if self.executed:
            status = "ส่งแล้ว"
        elif self.approved:
            status = "อนุมัติแล้ว รอส่ง"
        
        signal_value = self.signal.signal.value if isinstance(self.signal.signal, SignalType) else str(self.signal.signal)
        
        return (
            f"Trade Ticket #{self.id}\n"
            f"สถานะ: {status}\n"
            f"สัญลักษณ์: {self.signal.symbol}\n"
            f"ทิศทาง: {signal_value}\n"
            f"ขนาด: {self.lot_size:.2f} lot\n"
            f"Entry: {self.signal.entry_price:.5f}\n"
            f"SL: {self.signal.stop_loss:.5f}\n"
            f"TP: {self.signal.take_profit:.5f}\n"
            f"กลยุทธ์: {self.signal.strategy.value}\n"
            f"เหตุผล: {self.signal.reason}"
        )


class ExecutionEngine:
    """
    เครื่องมือส่งคำสั่งซื้อขาย - ส่วนที่ 2 ของระบบ
    หน้าที่: รับสัญญาณ → ตรวจสอบความเสี่ยง → ดำเนินการตามโหมด
    """
    
    def __init__(self, mt5_handler: MT5Handler, risk_manager: RiskManager):
        self.mt5 = mt5_handler
        self.risk = risk_manager
        self.pending_tickets: Dict[str, TradeTicket] = {}
        self.ticket_counter = 0
        self.execution_log = []
        
        # Callback สำหรับแจ้งเตือน
        self.notification_callback: Optional[Callable] = None
    
    def set_notification_callback(self, callback: Callable):
        """ตั้งค่า callback สำหรับการแจ้งเตือน"""
        self.notification_callback = callback
    
    def _notify(self, message: str, level: str = "info"):
        """ส่งการแจ้งเตือน"""
        if self.notification_callback:
            self.notification_callback(message, level)
        else:
            print(f"[{level.upper()}] {message}")
    
    def process_signal(self, signal: TradingSignal) -> Dict:
        """
        ประมวลผลสัญญาณตามโหมดที่เลือก
        
        Args:
            signal: สัญญาณจาก Signal Engine
            
        Returns:
            dict: ผลลัพธ์การประมวลผล
        """
        mode = get_execution_mode()
        
        # ดึงข้อมูลบัญชี
        account_info = self.mt5.get_account_info()
        if not account_info:
            return {'success': False, 'message': 'ไม่สามารถดึงข้อมูลบัญชีได้'}
        
        equity = account_info['equity']
        
        # ดึงข้อมูลตลาด
        market_info = self.mt5.get_symbol_info(signal.symbol)
        if not market_info:
            return {'success': False, 'message': f'ไม่สามารถดึงข้อมูล {signal.symbol} ได้'}
        
        # ดึงจำนวน positions ปัจจุบัน
        current_positions = self.mt5.get_current_positions_count()
        
        # ตรวจสอบความเสี่ยง
        approved, reason, lot_size = self.risk.check_signal(
            signal, equity, current_positions, market_info
        )
        
        if not approved:
            # ไม่แสดง warning สำหรับ NO_TRADE เพราะเป็นเรื่องปกติ
            if signal.signal.value != 'NO_TRADE':
                self._notify(f"❌ สัญญาณถูกปฏิเสธ: {reason}", "warning")
            return {
                'success': False,
                'message': f'ไม่ผ่านการตรวจสอบความเสี่ยง: {reason}',
                'signal': signal.to_dict()
            }
        
        # ดำเนินการตามโหมด
        if mode == ExecutionMode.DRY_RUN:
            return self._execute_dry_run(signal, lot_size, reason)
        
        elif mode == ExecutionMode.MANUAL_CONFIRM:
            return self._execute_manual_confirm(signal, lot_size, reason)
        
        elif mode == ExecutionMode.AUTO:
            return self._execute_auto(signal, lot_size, market_info)
        
        return {'success': False, 'message': 'โหมดการทำงานไม่ถูกต้อง'}
    
    def _execute_dry_run(self, signal: TradingSignal, lot_size: float, reason: str) -> Dict:
        """
        โหมด DRY_RUN: บันทึกและแจ้งเตือนเท่านั้น
        """
        self._notify(f"📊 [DRY RUN] สัญญาณ {signal.symbol}", "info")
        self._notify(f"  ทิศทาง: {signal.signal.value if isinstance(signal.signal, SignalType) else str(signal.signal)}", "info")
        self._notify(f"  ขนาด: {lot_size:.2f} lot", "info")
        self._notify(f"  Entry: {signal.entry_price:.5f}", "info")
        self._notify(f"  SL: {signal.stop_loss:.5f} | TP: {signal.take_profit:.5f}", "info")
        self._notify(f"  เหตุผล: {reason}", "info")
        
        # บันทึก log
        log_entry = {
            'timestamp': datetime.now(),
            'mode': 'DRY_RUN',
            'signal': signal.to_dict(),
            'lot_size': lot_size,
            'reason': reason,
            'executed': False
        }
        self.execution_log.append(log_entry)
        
        return {
            'success': True,
            'message': 'บันทึกสัญญาณสำเร็จ (DRY_RUN)',
            'mode': 'DRY_RUN',
            'signal': signal.to_dict(),
            'lot_size': lot_size
        }
    
    def _execute_manual_confirm(self, signal: TradingSignal, lot_size: float, reason: str) -> Dict:
        """
        โหมด MANUAL_CONFIRM: สร้างตั๋วคำสั่งรอยืนยัน
        """
        # สร้าง Trade Ticket
        self.ticket_counter += 1
        ticket_id = f"T{datetime.now().strftime('%Y%m%d')}_{self.ticket_counter:04d}"
        
        ticket = TradeTicket(
            id=ticket_id,
            signal=signal,
            lot_size=lot_size
        )
        
        self.pending_tickets[ticket_id] = ticket
        
        self._notify(f"🎫 สร้างตั๋วคำสั่ง #{ticket_id}", "info")
        self._notify(f"  {signal.symbol} {signal.signal.value if isinstance(signal.signal, SignalType) else str(signal.signal)} | {lot_size:.2f} lot", "info")
        self._notify(f"  รอการยืนยัน...", "warning")
        
        return {
            'success': True,
            'message': f'สร้างตั๋วคำสั่ง #{ticket_id} รอยืนยัน',
            'mode': 'MANUAL_CONFIRM',
            'ticket_id': ticket_id,
            'ticket': str(ticket)
        }
    
    def _execute_auto(self, signal: TradingSignal, lot_size: float, market_info: Dict) -> Dict:
        """
        โหมด AUTO: ส่งคำสั่งอัตโนมัติ
        """
        signal_type = signal.signal.value if isinstance(signal.signal, SignalType) else str(signal.signal)
        
        self._notify(f"🤖 [AUTO] ส่งคำสั่ง {signal.symbol} {signal_type}", "info")
        
        # ส่งคำสั่ง
        success, message, ticket_number = self.mt5.send_order(
            symbol=signal.symbol,
            order_type=signal_type,
            volume=lot_size,
            price=signal.entry_price,
            sl=signal.stop_loss,
            tp=signal.take_profit,
            comment=f"{signal.strategy.value}",
            magic=234000
        )
        
        # ตรวจสอบ slippage
        if success and ticket_number:
            positions = self.mt5.get_positions()
            if positions:
                for pos in positions:
                    if pos['ticket'] == ticket_number:
                        executed_price = pos['price_open']
                        acceptable, slippage_points = self.risk.check_max_slippage(
                            signal.entry_price, executed_price, market_info['point']
                        )
                        
                        if not acceptable:
                            self._notify(f"⚠️ Slippage สูงเกินไป: {slippage_points:.1f} points", "warning")
        
        # บันทึกผล
        log_entry = {
            'timestamp': datetime.now(),
            'mode': 'AUTO',
            'signal': signal.to_dict(),
            'lot_size': lot_size,
            'success': success,
            'message': message,
            'ticket_number': ticket_number,
            'executed': success
        }
        self.execution_log.append(log_entry)
        
        if success:
            self._notify(f"✅ ส่งคำสั่งสำเร็จ | Ticket: {ticket_number}", "success")
            # บันทึกการเทรดใน risk manager (จะอัปเดตกำไร/ขาดทุนทีหลัง)
            self.risk.record_trade(signal.symbol, 0.0)
        else:
            self._notify(f"❌ ส่งคำสั่งล้มเหลว: {message}", "error")
        
        return {
            'success': success,
            'message': message,
            'mode': 'AUTO',
            'ticket_number': ticket_number,
            'signal': signal.to_dict(),
            'lot_size': lot_size
        }
    
    def approve_ticket(self, ticket_id: str) -> Dict:
        """
        อนุมัติตั๋วคำสั่ง (สำหรับโหมด MANUAL_CONFIRM)
        
        Args:
            ticket_id: รหัสตั๋ว
            
        Returns:
            dict: ผลลัพธ์
        """
        if ticket_id not in self.pending_tickets:
            return {'success': False, 'message': f'ไม่พบตั๋ว #{ticket_id}'}
        
        ticket = self.pending_tickets[ticket_id]
        
        if ticket.executed:
            return {'success': False, 'message': 'ตั๋วนี้ถูกส่งแล้ว'}
        
        # อนุมัติ
        ticket.approved = True
        
        # ส่งคำสั่ง
        signal = ticket.signal
        signal_type = signal.signal.value if isinstance(signal.signal, SignalType) else str(signal.signal)
        
        success, message, ticket_number = self.mt5.send_order(
            symbol=signal.symbol,
            order_type=signal_type,
            volume=ticket.lot_size,
            price=signal.entry_price,
            sl=signal.stop_loss,
            tp=signal.take_profit,
            comment=f"{signal.strategy.value}",
            magic=234000
        )
        
        # อัปเดตตั๋ว
        ticket.executed = True
        ticket.ticket_number = ticket_number
        ticket.execution_time = datetime.now()
        ticket.result_message = message
        
        if success:
            self._notify(f"✅ ส่งตั๋ว #{ticket_id} สำเร็จ | Ticket: {ticket_number}", "success")
            self.risk.record_trade(signal.symbol, 0.0)
        else:
            self._notify(f"❌ ส่งตั๋ว #{ticket_id} ล้มเหลว: {message}", "error")
        
        return {
            'success': success,
            'message': message,
            'ticket_id': ticket_id,
            'ticket_number': ticket_number
        }
    
    def reject_ticket(self, ticket_id: str) -> Dict:
        """
        ปฏิเสธตั๋วคำสั่ง
        
        Args:
            ticket_id: รหัสตั๋ว
            
        Returns:
            dict: ผลลัพธ์
        """
        if ticket_id not in self.pending_tickets:
            return {'success': False, 'message': f'ไม่พบตั๋ว #{ticket_id}'}
        
        ticket = self.pending_tickets[ticket_id]
        
        if ticket.executed:
            return {'success': False, 'message': 'ตั๋วนี้ถูกส่งแล้ว ไม่สามารถปฏิเสธได้'}
        
        # ลบตั๋ว
        del self.pending_tickets[ticket_id]
        
        self._notify(f"🚫 ปฏิเสธตั๋ว #{ticket_id}", "info")
        
        return {
            'success': True,
            'message': f'ปฏิเสธตั๋ว #{ticket_id} แล้ว'
        }
    
    def get_pending_tickets(self) -> List[TradeTicket]:
        """ดึงรายการตั๋วที่รอยืนยัน"""
        return [t for t in self.pending_tickets.values() if not t.executed]
    
    def get_executed_tickets(self) -> List[TradeTicket]:
        """ดึงรายการตั๋วที่ส่งแล้ว"""
        return [t for t in self.pending_tickets.values() if t.executed]
    
    def get_execution_log(self, limit: int = 50) -> List[Dict]:
        """
        ดึง log การดำเนินการ
        
        Args:
            limit: จำนวนรายการสูงสุด
            
        Returns:
            list ของ log entries
        """
        return self.execution_log[-limit:]


# ตัวอย่างการใช้งาน
if __name__ == "__main__":
    import numpy as np
    from signal_engine import SignalEngine
    from config import StrategyType, set_execution_mode, ExecutionMode
    
    # เชื่อมต่อ MT5
    mt5 = MT5Handler()
    success, msg = mt5.connect()
    if not success:
        print(f"ไม่สามารถเชื่อมต่อ MT5: {msg}")
        exit()
    
    # สร้าง engines
    risk_mgr = RiskManager()
    signal_engine = SignalEngine()
    exec_engine = ExecutionEngine(mt5, risk_mgr)
    
    # ตั้งโหมดเป็น DRY_RUN
    set_execution_mode(ExecutionMode.DRY_RUN)
    
    # ดึงข้อมูลจริงจาก MT5
    symbol = "EURUSD"
    data = mt5.get_historical_data(symbol, "D1", 100)
    
    if data:
        high = np.array(data['high'])
        low = np.array(data['low'])
        close = np.array(data['close'])
        
        # สร้างสัญญาณ
        signal = signal_engine.generate_signal(
            symbol, StrategyType.MA_CROSSOVER, high, low, close
        )
        
        print(f"\n{signal}\n")
        
        # ส่งสัญญาณไปยัง Execution Engine
        result = exec_engine.process_signal(signal)
        print(f"\nผลลัพธ์: {result}")
    
    mt5.disconnect()
