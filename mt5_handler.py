"""
MT5 Handler Module
จัดการการเชื่อมต่อและดึงข้อมูลจาก MetaTrader5
"""

import MetaTrader5 as mt5
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple


class MT5Handler:
    """คลาสสำหรับจัดการการเชื่อมต่อและดึงข้อมูลจาก MT5"""
    
    def __init__(self):
        self.is_connected = False
    
    def connect(self) -> tuple[bool, str]:
        """
        เชื่อมต่อกับ MetaTrader5
        
        Returns:
            tuple: (สำเร็จหรือไม่, ข้อความ)
        """
        try:
            if not mt5.initialize():
                error = mt5.last_error()
                return False, f"ไม่สามารถเชื่อมต่อ MT5: {error}"
            
            self.is_connected = True
            return True, "เชื่อมต่อ MT5 สำเร็จ!"
            
        except Exception as e:
            return False, f"เกิดข้อผิดพลาด: {str(e)}"
    
    def disconnect(self) -> tuple[bool, str]:
        """
        ตัดการเชื่อมต่อจาก MT5
        
        Returns:
            tuple: (สำเร็จหรือไม่, ข้อความ)
        """
        try:
            mt5.shutdown()
            self.is_connected = False
            return True, "ตัดการเชื่อมต่อ MT5 สำเร็จ!"
            
        except Exception as e:
            return False, f"เกิดข้อผิดพลาด: {str(e)}"
    
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        ดึงข้อมูลบัญชี
        
        Returns:
            dict: ข้อมูลบัญชีหรือ None
        """
        try:
            account_info = mt5.account_info()
            if account_info is None:
                return None
            
            return {
                'login': account_info.login,
                'company': account_info.company,
                'server': account_info.server,
                'currency': account_info.currency,
                'balance': account_info.balance,
                'profit': account_info.profit,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'margin_free': account_info.margin_free,
                'margin_level': account_info.margin_level
            }
            
        except Exception as e:
            print(f"Error getting account info: {e}")
            return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        ดึงข้อมูลราคาของสัญลักษณ์
        
        Args:
            symbol: ชื่อสัญลักษณ์
            
        Returns:
            dict: ข้อมูลสัญลักษณ์หรือ None
        """
        try:
            symbol = symbol.upper()
            
            # ตรวจสอบว่าสัญลักษณ์มีอยู่หรือไม่
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return None
            
            # ดึงข้อมูล tick ล่าสุด
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return None
            
            return {
                'symbol': symbol,
                'time': datetime.fromtimestamp(tick.time),
                'bid': tick.bid,
                'ask': tick.ask,
                'last': tick.last,
                'volume': tick.volume,
                'spread': symbol_info.spread,
                'digits': symbol_info.digits,
                'point': symbol_info.point,
                'trade_mode': symbol_info.trade_mode,
                'contract_size': symbol_info.trade_contract_size,
                'volume_min': symbol_info.volume_min,
                'volume_max': symbol_info.volume_max,
                'volume_step': symbol_info.volume_step
            }
            
        except Exception as e:
            print(f"Error getting symbol info: {e}")
            return None
    
    def get_positions(self) -> Optional[List[Dict[str, Any]]]:
        """
        ดึงข้อมูลออเดอร์ที่เปิดอยู่
        
        Returns:
            list: รายการออเดอร์หรือ None
        """
        try:
            positions = mt5.positions_get()
            
            if positions is None:
                return None
            
            if len(positions) == 0:
                return []
            
            position_list = []
            for pos in positions:
                position_type = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                position_list.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': position_type,
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'profit': pos.profit,
                    'time': datetime.fromtimestamp(pos.time),
                    'comment': pos.comment
                })
            
            return position_list
            
        except Exception as e:
            print(f"Error getting positions: {e}")
            return None
    
    def get_historical_data(self, symbol: str, timeframe: str, num_bars: int = 500) -> Optional[Dict[str, Any]]:
        """
        ดึงข้อมูลแท่งเทียนย้อนหลัง
        
        Args:
            symbol: ชื่อสัญลักษณ์
            timeframe: กรอบเวลา เช่น "D1", "H1", "M15"
            num_bars: จำนวนแท่งที่ต้องการ (default: 500 สำหรับ Ultimate Strategy)
            
        Returns:
            dict: {'high': [], 'low': [], 'close': [], 'open': [], 'time': [], 'volume': []}
        """
        try:
            # แปลง timeframe string เป็น MT5 constant
            timeframe_map = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15,
                'M30': mt5.TIMEFRAME_M30,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1,
                'W1': mt5.TIMEFRAME_W1,
                'MN1': mt5.TIMEFRAME_MN1
            }
            
            mt5_timeframe = timeframe_map.get(timeframe, mt5.TIMEFRAME_D1)
            
            # ดึงข้อมูล
            rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, num_bars)
            
            if rates is None or len(rates) == 0:
                return None
            
            return {
                'time': [datetime.fromtimestamp(r['time']) for r in rates],
                'open': [r['open'] for r in rates],
                'high': [r['high'] for r in rates],
                'low': [r['low'] for r in rates],
                'close': [r['close'] for r in rates],
                'volume': [r['tick_volume'] for r in rates]
            }
            
        except Exception as e:
            print(f"Error getting historical data: {e}")
            return None
    
    def get_current_positions_count(self) -> Dict[str, int]:
        """
        นับจำนวน positions ที่เปิดอยู่ต่อสัญลักษณ์
        
        Returns:
            dict: {symbol: count}
        """
        try:
            positions = self.get_positions()
            if not positions:
                return {}
            
            symbol_count = {}
            for pos in positions:
                symbol = pos['symbol']
                symbol_count[symbol] = symbol_count.get(symbol, 0) + 1
            
            return symbol_count
            
        except Exception as e:
            print(f"Error counting positions: {e}")
            return {}
    
    def check_trading_enabled(self) -> Tuple[bool, str]:
        """
        ตรวจสอบว่า Algo Trading เปิดอยู่หรือไม่
        
        Returns:
            (เปิดอยู่: bool, ข้อความ: str)
        """
        try:
            terminal_info = mt5.terminal_info()
            if terminal_info is None:
                return False, "ไม่สามารถตรวจสอบสถานะ Terminal"
            
            if not terminal_info.trade_allowed:
                return False, "❌ Algo Trading ถูกปิดอยู่!\n\nวิธีเปิด:\n1. เปิด MT5\n2. ไปที่ Tools → Options → Expert Advisors\n3. เปิด 'Allow automated trading'\n4. หรือกดปุ่ม 'Algo Trading' บน toolbar ให้เป็นสีเขียว"
            
            return True, "Algo Trading เปิดอยู่"
        except Exception as e:
            return False, f"เกิดข้อผิดพลาด: {str(e)}"
    
    def send_order(self, symbol: str, order_type: str, volume: float,
                  price: float, sl: float = 0.0, tp: float = 0.0,
                  comment: str = "", magic: int = 234000) -> Tuple[bool, str, Optional[int]]:
        """
        ส่งคำสั่งซื้อขาย
        
        Args:
            symbol: ชื่อสัญลักษณ์
            order_type: "BUY" หรือ "SELL"
            volume: ขนาด lot
            price: ราคาที่ต้องการเข้า (ใช้สำหรับ market order)
            sl: Stop Loss
            tp: Take Profit
            comment: คอมเมนต์
            magic: Magic number
            
        Returns:
            (สำเร็จ: bool, ข้อความ: str, ticket: int)
        """
        try:
            # ตรวจสอบ Algo Trading ก่อน
            trading_enabled, msg = self.check_trading_enabled()
            if not trading_enabled:
                return False, msg, None
            
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return False, f"ไม่พบสัญลักษณ์ {symbol}", None
            
            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    return False, f"ไม่สามารถเลือกสัญลักษณ์ {symbol}", None
            
            # กำหนดประเภทคำสั่ง
            if order_type.upper() == "BUY":
                order_type_mt5 = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(symbol).ask
            elif order_type.upper() == "SELL":
                order_type_mt5 = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(symbol).bid
            else:
                return False, f"ประเภทคำสั่งไม่ถูกต้อง: {order_type}", None
            
            # ปัดเศษ volume ให้ถูกต้อง
            volume = round(volume / symbol_info.volume_step) * symbol_info.volume_step
            volume = max(symbol_info.volume_min, min(volume, symbol_info.volume_max))
            
            # ปัดเศษ SL/TP
            digits = symbol_info.digits
            if sl > 0:
                sl = round(sl, digits)
            if tp > 0:
                tp = round(tp, digits)
            
            # ตรวจสอบ filling mode ที่รองรับ
            filling_modes = []
            if symbol_info.filling_mode & 1:  # FOK
                filling_modes.append(mt5.ORDER_FILLING_FOK)
            if symbol_info.filling_mode & 2:  # IOC
                filling_modes.append(mt5.ORDER_FILLING_IOC)
            if symbol_info.filling_mode & 4:  # Return
                filling_modes.append(mt5.ORDER_FILLING_RETURN)
            
            # ถ้าไม่มี filling mode ที่รองรับ ให้ใช้ IOC
            if not filling_modes:
                filling_modes = [mt5.ORDER_FILLING_IOC]
            
            # ลองส่งคำสั่งด้วย filling mode ต่างๆ
            last_error = None
            for filling_type in filling_modes:
                # สร้าง request
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": volume,
                    "type": order_type_mt5,
                    "price": price,
                    "sl": sl,
                    "tp": tp,
                    "magic": magic,
                    "comment": comment,
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": filling_type,
                }
                
                # ส่งคำสั่ง
                result = mt5.order_send(request)
                
                if result is None:
                    last_error = "ไม่สามารถส่งคำสั่งได้"
                    continue
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    return True, "ส่งคำสั่งสำเร็จ", result.order
                
                # เก็บ error ไว้ลองต่อ
                last_error = self._get_error_message(result.retcode, result.comment)
                
                # ถ้าเป็น error ที่ไม่เกี่ยวกับ filling mode ให้หยุดทันที
                if result.retcode not in [10030, 10031, 10032]:  # Long only, Short only, Close only
                    break
            
            # ถ้าลองทุก filling mode แล้วยังไม่ได้ ให้คืนค่า error สุดท้าย
            return False, last_error or "ไม่สามารถส่งคำสั่งได้", None
            
        except Exception as e:
            return False, f"เกิดข้อผิดพลาด: {str(e)}", None
    
    def _get_error_message(self, retcode: int, original_msg: str) -> str:
        """
        แปล error code เป็นข้อความที่เข้าใจง่าย
        """
        error_messages = {
            10004: "❌ คำสั่งถูกปฏิเสธ (Requote) - ลองใหม่อีกครั้ง",
            10006: "❌ คำสั่งถูกปฏิเสธ - กรุณาลองใหม่",
            10007: "❌ คำสั่งถูกยกเลิก",
            10008: "❌ คำสั่งอยู่ในคิว",
            10009: "❌ คำสั่งเสร็จสมบูรณ์แล้ว",
            10010: "❌ คำสั่งถูกปฏิเสธบางส่วน",
            10011: "❌ Parameter ผิดพลาด - ตรวจสอบ lot size และราคา",
            10012: "❌ Volume ไม่ถูกต้อง - ตรวจสอบ lot size",
            10013: "❌ ราคาไม่ถูกต้อง",
            10014: "❌ Stop Loss/Take Profit ไม่ถูกต้อง",
            10015: "❌ คำสั่งหมดอายุ",
            10016: "❌ คำสั่งถูกเปลี่ยนแปลง",
            10018: "❌ ตลาดปิดอยู่ - รอตลาดเปิด",
            10019: "❌ เงินในบัญชีไม่เพียงพอ - Margin ไม่พอ",
            10020: "❌ ราคาเปลี่ยนแปลง (Freeze level)",
            10021: "❌ Stop Loss/TP อยู่ใกล้ราคาปัจจุบันเกินไป",
            10025: "❌ ไม่มี error แต่ส่งไม่สำเร็จ",
            10027: "❌ Algo Trading ถูกปิดอยู่!\n\nวิธีเปิด:\n1. เปิด MT5\n2. กดปุ่ม 'Algo Trading' บน toolbar ให้เป็นสีเขียว\n3. หรือไปที่ Tools → Options → Expert Advisors\n4. เปิด 'Allow automated trading'",
            10028: "❌ Position ถูกปิดแล้ว",
            10029: "❌ คำสั่งถูกล็อค",
            10030: "❌ คำสั่งถูกปิด (Long only)",
            10031: "❌ คำสั่งถูกปิด (Short only)",
            10032: "❌ คำสั่งถูกปิด (Close only)",
            10033: "❌ Position ถูกปิดโดย Stop Out",
            10034: "❌ Position หมดอายุ",
            10035: "❌ การเปลี่ยนแปลงถูกปฏิเสธ",
            10036: "❌ ถูกจำกัดจำนวน position",
        }
        
        if retcode in error_messages:
            return error_messages[retcode]
        else:
            return f"❌ คำสั่งล้มเหลว: {original_msg} (code: {retcode})"
    
    def close_position(self, ticket: int) -> Tuple[bool, str]:
        """
        ปิด position
        
        Args:
            ticket: หมายเลข ticket
            
        Returns:
            (สำเร็จ: bool, ข้อความ: str)
        """
        try:
            position = mt5.positions_get(ticket=ticket)
            if position is None or len(position) == 0:
                return False, f"ไม่พบ position ticket {ticket}"
            
            position = position[0]
            
            # กำหนดประเภทการปิด (ตรงข้ามกับการเปิด)
            if position.type == mt5.POSITION_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(position.symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(position.symbol).ask
            
            # สร้าง request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": order_type,
                "position": ticket,
                "price": price,
                "magic": position.magic,
                "comment": "close by bot",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # ส่งคำสั่ง
            result = mt5.order_send(request)
            
            if result is None:
                return False, "ไม่สามารถปิด position ได้"
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return False, f"ปิด position ล้มเหลว: {result.comment}"
            
            return True, "ปิด position สำเร็จ"
            
        except Exception as e:
            return False, f"เกิดข้อผิดพลาด: {str(e)}"
    
    def modify_position(self, ticket: int, sl: float = None, tp: float = None) -> Tuple[bool, str]:
        """
        แก้ไข SL/TP ของ position
        
        Args:
            ticket: หมายเลข ticket
            sl: Stop Loss ใหม่ (None = ไม่เปลี่ยน)
            tp: Take Profit ใหม่ (None = ไม่เปลี่ยน)
            
        Returns:
            (สำเร็จ: bool, ข้อความ: str)
        """
        try:
            position = mt5.positions_get(ticket=ticket)
            if position is None or len(position) == 0:
                return False, f"ไม่พบ position ticket {ticket}"
            
            position = position[0]
            symbol_info = mt5.symbol_info(position.symbol)
            
            # ใช้ค่าเดิมถ้าไม่ระบุ
            if sl is None:
                sl = position.sl
            else:
                sl = round(sl, symbol_info.digits)
            
            if tp is None:
                tp = position.tp
            else:
                tp = round(tp, symbol_info.digits)
            
            # สร้าง request
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": position.symbol,
                "position": ticket,
                "sl": sl,
                "tp": tp,
            }
            
            # ส่งคำสั่ง
            result = mt5.order_send(request)
            
            if result is None:
                return False, "ไม่สามารถแก้ไข position ได้"
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return False, f"แก้ไข position ล้มเหลว: {result.comment}"
            
            return True, "แก้ไข position สำเร็จ"
            
        except Exception as e:
            return False, f"เกิดข้อผิดพลาด: {str(e)}"
