"""
Position Manager - ระบบจัดการ Position อัตโนมัติ
รองรับ: Trailing Stop, Break Even, Partial Close
"""

from typing import Dict, List, Optional
from datetime import datetime
import MetaTrader5 as mt5


class PositionManager:
    """จัดการ Position ที่เปิดอยู่อัตโนมัติ"""
    
    def __init__(self, mt5_handler):
        self.mt5_handler = mt5_handler
        self.monitored_positions = {}  # {ticket: settings}
        
        # การตั้งค่าเริ่มต้น
        self.enable_trailing = True
        self.enable_breakeven = True
        self.enable_partial_close = True
        
        # พารามิเตอร์
        self.trailing_step_pips = 10  # ปรับ SL ทุก 10 pips
        self.breakeven_trigger_pips = 20  # ย้าย SL ไป BE เมื่อกำไร 20 pips
        self.partial_close_percent = 50  # ปิด 50% ของ position
        self.partial_close_trigger_pips = 30  # ปิดบางส่วนเมื่อกำไร 30 pips
    
    def add_position(self, ticket: int, strategy: str = "", entry_price: float = 0.0):
        """เพิ่ม position เข้าระบบ monitor"""
        self.monitored_positions[ticket] = {
            'strategy': strategy,
            'entry_price': entry_price,
            'breakeven_moved': False,
            'partial_closed': False,
            'highest_profit': 0.0,
            'added_time': datetime.now()
        }
    
    def remove_position(self, ticket: int):
        """ลบ position ออกจากระบบ monitor"""
        if ticket in self.monitored_positions:
            del self.monitored_positions[ticket]
    
    def monitor_all_positions(self) -> Dict:
        """ตรวจสอบ position ทั้งหมดและทำการจัดการอัตโนมัติ"""
        results = {
            'checked': 0,
            'trailing_updated': 0,
            'breakeven_moved': 0,
            'partial_closed': 0,
            'messages': []
        }
        
        positions = self.mt5_handler.get_positions()
        if not positions:
            return results
        
        results['checked'] = len(positions)
        
        for pos in positions:
            ticket = pos['ticket']
            symbol = pos['symbol']
            pos_type = pos['type']  # 0=BUY, 1=SELL
            volume = pos['volume']
            entry_price = pos['price_open']
            current_price = pos['price_current']
            sl = pos['sl']
            tp = pos['tp']
            profit = pos['profit']
            
            # เพิ่ม position ถ้ายังไม่มี
            if ticket not in self.monitored_positions:
                self.add_position(ticket, "", entry_price)
            
            pos_data = self.monitored_positions[ticket]
            
            # ดึงข้อมูล symbol
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                continue
            
            point = symbol_info.point
            digits = symbol_info.digits
            
            # คำนวณกำไรเป็น pips
            if pos_type == 0:  # BUY
                profit_pips = (current_price - entry_price) / point
            else:  # SELL
                profit_pips = (entry_price - current_price) / point
            
            # อัปเดตกำไรสูงสุด
            if profit_pips > pos_data['highest_profit']:
                pos_data['highest_profit'] = profit_pips
            
            # === 1. BREAK EVEN ===
            if self.enable_breakeven and not pos_data['breakeven_moved']:
                if profit_pips >= self.breakeven_trigger_pips:
                    new_sl = entry_price + (5 * point if pos_type == 0 else -5 * point)  # +5 pips จาก entry
                    
                    if self._modify_position(ticket, symbol, new_sl, tp):
                        pos_data['breakeven_moved'] = True
                        results['breakeven_moved'] += 1
                        results['messages'].append(
                            f"✅ Break Even: {symbol} Ticket#{ticket} | กำไร: {profit_pips:.1f} pips"
                        )
            
            # === 2. PARTIAL CLOSE ===
            if self.enable_partial_close and not pos_data['partial_closed']:
                if profit_pips >= self.partial_close_trigger_pips and volume >= 0.02:
                    close_volume = round(volume * (self.partial_close_percent / 100), 2)
                    close_volume = max(0.01, close_volume)  # ต่ำสุด 0.01 lot
                    
                    if self._partial_close_position(ticket, symbol, close_volume, pos_type):
                        pos_data['partial_closed'] = True
                        results['partial_closed'] += 1
                        results['messages'].append(
                            f"💰 Partial Close: {symbol} Ticket#{ticket} | ปิด {close_volume} lot | กำไร: {profit_pips:.1f} pips"
                        )
            
            # === 3. TRAILING STOP ===
            if self.enable_trailing and pos_data['breakeven_moved']:
                # ใช้ trailing เมื่อผ่าน breakeven แล้ว
                if pos_type == 0:  # BUY
                    new_sl = current_price - (self.trailing_step_pips * point)
                    if new_sl > sl + (5 * point):  # ต้องดีขึ้นอย่างน้อย 5 pips
                        if self._modify_position(ticket, symbol, new_sl, tp):
                            results['trailing_updated'] += 1
                            results['messages'].append(
                                f"📈 Trailing: {symbol} Ticket#{ticket} | SL: {new_sl:.{digits}f} | กำไร: {profit_pips:.1f} pips"
                            )
                else:  # SELL
                    new_sl = current_price + (self.trailing_step_pips * point)
                    if sl == 0 or new_sl < sl - (5 * point):
                        if self._modify_position(ticket, symbol, new_sl, tp):
                            results['trailing_updated'] += 1
                            results['messages'].append(
                                f"📉 Trailing: {symbol} Ticket#{ticket} | SL: {new_sl:.{digits}f} | กำไร: {profit_pips:.1f} pips"
                            )
        
        return results
    
    def _modify_position(self, ticket: int, symbol: str, new_sl: float, tp: float) -> bool:
        """แก้ไข SL/TP ของ position"""
        try:
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return False
            
            digits = symbol_info.digits
            new_sl = round(new_sl, digits)
            tp = round(tp, digits) if tp > 0 else 0.0
            
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "symbol": symbol,
                "sl": new_sl,
                "tp": tp,
            }
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error modifying position: {e}")
            return False
    
    def _partial_close_position(self, ticket: int, symbol: str, volume: float, pos_type: int) -> bool:
        """ปิด position บางส่วน"""
        try:
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return False
            
            # ปัดเศษ volume
            volume = round(volume / symbol_info.volume_step) * symbol_info.volume_step
            volume = max(symbol_info.volume_min, volume)
            
            # ดึงราคาปัจจุบัน
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return False
            
            price = tick.bid if pos_type == 0 else tick.ask
            
            # สร้างคำสั่งปิดบางส่วน
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "symbol": symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_SELL if pos_type == 0 else mt5.ORDER_TYPE_BUY,
                "price": price,
                "magic": 234000,
                "comment": "Partial Close",
            }
            
            # ลองหา filling mode ที่ใช้ได้
            filling_modes = []
            if symbol_info.filling_mode & 1:
                filling_modes.append(mt5.ORDER_FILLING_FOK)
            if symbol_info.filling_mode & 2:
                filling_modes.append(mt5.ORDER_FILLING_IOC)
            if symbol_info.filling_mode & 4:
                filling_modes.append(mt5.ORDER_FILLING_RETURN)
            
            if not filling_modes:
                filling_modes = [mt5.ORDER_FILLING_IOC]
            
            for filling in filling_modes:
                request["type_filling"] = filling
                result = mt5.order_send(request)
                
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error partial closing position: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """ดึงสถิติการจัดการ position"""
        return {
            'monitored_positions': len(self.monitored_positions),
            'trailing_enabled': self.enable_trailing,
            'breakeven_enabled': self.enable_breakeven,
            'partial_close_enabled': self.enable_partial_close,
            'settings': {
                'trailing_step': self.trailing_step_pips,
                'breakeven_trigger': self.breakeven_trigger_pips,
                'partial_close_percent': self.partial_close_percent,
                'partial_close_trigger': self.partial_close_trigger_pips
            }
        }
    
    def clear_all(self):
        """ล้างข้อมูล position ทั้งหมด"""
        self.monitored_positions.clear()
