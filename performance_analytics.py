"""
Performance Analytics Module
โมดูลวิเคราะห์ผลการเทรดแบบละเอียด
คำนวณ Metrics ต่างๆ เช่น Sharpe Ratio, Max Drawdown, Profit Factor
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class TradeRecord:
    """บันทึกการเทรด 1 ไม้"""
    ticket: int
    symbol: str
    type: str  # "BUY" or "SELL"
    lot_size: float
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    profit: float
    pips: float
    strategy: str
    comment: str = ""
    
    @property
    def duration(self) -> timedelta:
        """ระยะเวลาที่ถือไม้"""
        return self.exit_time - self.entry_time
    
    @property
    def is_win(self) -> bool:
        """เป็นไม้ชนะหรือไม่"""
        return self.profit > 0
    
    @property
    def is_loss(self) -> bool:
        """เป็นไม้ขาดทุนหรือไม่"""
        return self.profit < 0


class PerformanceAnalytics:
    """
    คลาสสำหรับวิเคราะห์ผลการเทรด
    คำนวณ Metrics ต่างๆ เพื่อประเมินประสิทธิภาพของระบบ
    """
    
    def __init__(self):
        self.trades: List[TradeRecord] = []
        self.initial_balance = 0.0
        self.equity_curve: List[Tuple[datetime, float]] = []
    
    def add_trade(self, trade: TradeRecord):
        """เพิ่มบันทึกการเทรด"""
        self.trades.append(trade)
    
    def set_initial_balance(self, balance: float):
        """ตั้งค่ายอดเงินเริ่มต้น"""
        self.initial_balance = balance
    
    def calculate_metrics(self) -> Dict:
        """
        คำนวณ Performance Metrics ทั้งหมด
        
        Returns:
            dict: ผลลัพธ์การวิเคราะห์
        """
        if not self.trades:
            return self._empty_metrics()
        
        # แยกไม้ชนะ/แพ้
        winning_trades = [t for t in self.trades if t.is_win]
        losing_trades = [t for t in self.trades if t.is_loss]
        
        total_trades = len(self.trades)
        total_wins = len(winning_trades)
        total_losses = len(losing_trades)
        
        # คำนวณกำไร/ขาดทุน
        total_profit = sum(t.profit for t in winning_trades)
        total_loss = sum(abs(t.profit) for t in losing_trades)
        net_profit = sum(t.profit for t in self.trades)
        
        # คำนวณค่าเฉลี่ย
        avg_win = total_profit / total_wins if total_wins > 0 else 0
        avg_loss = total_loss / total_losses if total_losses > 0 else 0
        
        # Win Rate
        win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
        
        # Profit Factor
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # Risk/Reward Ratio
        risk_reward = avg_win / avg_loss if avg_loss > 0 else 0
        
        # Expectancy
        expectancy = (win_rate / 100 * avg_win) - ((1 - win_rate / 100) * avg_loss)
        
        # Largest Win/Loss
        largest_win = max((t.profit for t in winning_trades), default=0)
        largest_loss = min((t.profit for t in losing_trades), default=0)
        
        # Consecutive Wins/Losses
        max_consecutive_wins = self._max_consecutive_wins()
        max_consecutive_losses = self._max_consecutive_losses()
        
        # Drawdown
        max_drawdown, max_drawdown_pct = self._calculate_max_drawdown()
        
        # Sharpe Ratio (annualized)
        sharpe_ratio = self._calculate_sharpe_ratio()
        
        # Sortino Ratio
        sortino_ratio = self._calculate_sortino_ratio()
        
        # Average Trade Duration
        avg_duration = self._calculate_avg_duration()
        
        # Profit by Strategy
        profit_by_strategy = self._profit_by_strategy()
        
        # Win Rate by Strategy
        winrate_by_strategy = self._winrate_by_strategy()
        
        # ROI (Return on Investment)
        roi = (net_profit / self.initial_balance * 100) if self.initial_balance > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': total_wins,
            'losing_trades': total_losses,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'total_loss': total_loss,
            'net_profit': net_profit,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'profit_factor': profit_factor,
            'risk_reward_ratio': risk_reward,
            'expectancy': expectancy,
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'avg_duration': avg_duration,
            'profit_by_strategy': profit_by_strategy,
            'winrate_by_strategy': winrate_by_strategy,
            'roi': roi,
            'initial_balance': self.initial_balance,
            'final_balance': self.initial_balance + net_profit
        }
    
    def _empty_metrics(self) -> Dict:
        """ผลลัพธ์เมื่อยังไม่มีการเทรด"""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'net_profit': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'largest_win': 0.0,
            'largest_loss': 0.0,
            'profit_factor': 0.0,
            'risk_reward_ratio': 0.0,
            'expectancy': 0.0,
            'max_consecutive_wins': 0,
            'max_consecutive_losses': 0,
            'max_drawdown': 0.0,
            'max_drawdown_pct': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'avg_duration': '0h 0m',
            'profit_by_strategy': {},
            'winrate_by_strategy': {},
            'roi': 0.0,
            'initial_balance': self.initial_balance,
            'final_balance': self.initial_balance
        }
    
    def _max_consecutive_wins(self) -> int:
        """คำนวณจำนวนชนะติดต่อกันสูงสุด"""
        max_streak = 0
        current_streak = 0
        
        for trade in self.trades:
            if trade.is_win:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def _max_consecutive_losses(self) -> int:
        """คำนวณจำนวนขาดทุนติดต่อกันสูงสุด"""
        max_streak = 0
        current_streak = 0
        
        for trade in self.trades:
            if trade.is_loss:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def _calculate_max_drawdown(self) -> Tuple[float, float]:
        """
        คำนวณ Maximum Drawdown
        
        Returns:
            (max_drawdown_amount, max_drawdown_percentage)
        """
        if not self.trades:
            return 0.0, 0.0
        
        # สร้าง equity curve
        balance = self.initial_balance
        peak = balance
        max_dd = 0.0
        max_dd_pct = 0.0
        
        for trade in self.trades:
            balance += trade.profit
            
            if balance > peak:
                peak = balance
            else:
                dd = peak - balance
                dd_pct = (dd / peak * 100) if peak > 0 else 0
                
                if dd > max_dd:
                    max_dd = dd
                    max_dd_pct = dd_pct
        
        return max_dd, max_dd_pct
    
    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """
        คำนวณ Sharpe Ratio (annualized)
        
        Sharpe = (Average Return - Risk Free Rate) / Standard Deviation of Returns
        
        Args:
            risk_free_rate: อัตราผลตอบแทนปลอดความเสี่ยง (default: 2% per year)
        
        Returns:
            Sharpe Ratio
        """
        if not self.trades or len(self.trades) < 2:
            return 0.0
        
        # คำนวณ returns
        returns = np.array([t.profit / self.initial_balance for t in self.trades])
        
        # Average return
        avg_return = np.mean(returns)
        
        # Standard deviation
        std_dev = np.std(returns, ddof=1)
        
        if std_dev == 0:
            return 0.0
        
        # Sharpe Ratio (annualized - สมมติ 252 trading days)
        sharpe = (avg_return - risk_free_rate / 252) / std_dev * np.sqrt(252)
        
        return sharpe
    
    def _calculate_sortino_ratio(self, risk_free_rate: float = 0.02) -> float:
        """
        คำนวณ Sortino Ratio (คล้าย Sharpe แต่ใช้ Downside Deviation)
        
        Returns:
            Sortino Ratio
        """
        if not self.trades or len(self.trades) < 2:
            return 0.0
        
        returns = np.array([t.profit / self.initial_balance for t in self.trades])
        avg_return = np.mean(returns)
        
        # Downside deviation (เฉพาะ negative returns)
        negative_returns = returns[returns < 0]
        
        if len(negative_returns) == 0:
            return float('inf')
        
        downside_dev = np.std(negative_returns, ddof=1)
        
        if downside_dev == 0:
            return 0.0
        
        sortino = (avg_return - risk_free_rate / 252) / downside_dev * np.sqrt(252)
        
        return sortino
    
    def _calculate_avg_duration(self) -> str:
        """คำนวณระยะเวลาเฉลี่ยของการถือไม้"""
        if not self.trades:
            return "0h 0m"
        
        total_seconds = sum(t.duration.total_seconds() for t in self.trades)
        avg_seconds = total_seconds / len(self.trades)
        
        hours = int(avg_seconds // 3600)
        minutes = int((avg_seconds % 3600) // 60)
        
        return f"{hours}h {minutes}m"
    
    def _profit_by_strategy(self) -> Dict[str, float]:
        """กำไรแยกตามกลยุทธ์"""
        profit_dict = {}
        
        for trade in self.trades:
            if trade.strategy not in profit_dict:
                profit_dict[trade.strategy] = 0.0
            profit_dict[trade.strategy] += trade.profit
        
        return profit_dict
    
    def _winrate_by_strategy(self) -> Dict[str, float]:
        """Win rate แยกตามกลยุทธ์"""
        strategy_stats = {}
        
        for trade in self.trades:
            if trade.strategy not in strategy_stats:
                strategy_stats[trade.strategy] = {'wins': 0, 'total': 0}
            
            strategy_stats[trade.strategy]['total'] += 1
            if trade.is_win:
                strategy_stats[trade.strategy]['wins'] += 1
        
        winrate_dict = {}
        for strategy, stats in strategy_stats.items():
            winrate_dict[strategy] = (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0
        
        return winrate_dict
    
    def get_equity_curve_data(self) -> List[Tuple[datetime, float]]:
        """
        สร้างข้อมูล Equity Curve
        
        Returns:
            List of (datetime, balance)
        """
        if not self.trades:
            return []
        
        curve = [(self.trades[0].entry_time, self.initial_balance)]
        balance = self.initial_balance
        
        for trade in self.trades:
            balance += trade.profit
            curve.append((trade.exit_time, balance))
        
        return curve
    
    def get_drawdown_curve_data(self) -> List[Tuple[datetime, float]]:
        """
        สร้างข้อมูล Drawdown Curve
        
        Returns:
            List of (datetime, drawdown_percentage)
        """
        if not self.trades:
            return []
        
        balance = self.initial_balance
        peak = balance
        curve = []
        
        for trade in self.trades:
            balance += trade.profit
            
            if balance > peak:
                peak = balance
            
            dd_pct = ((peak - balance) / peak * 100) if peak > 0 else 0
            curve.append((trade.exit_time, dd_pct))
        
        return curve
    
    def export_to_dict(self) -> List[Dict]:
        """Export ข้อมูลการเทรดเป็น list of dict (สำหรับ export CSV)"""
        return [
            {
                'Ticket': t.ticket,
                'Symbol': t.symbol,
                'Type': t.type,
                'Lot': t.lot_size,
                'Entry Price': t.entry_price,
                'Exit Price': t.exit_price,
                'Entry Time': t.entry_time.strftime('%Y-%m-%d %H:%M:%S'),
                'Exit Time': t.exit_time.strftime('%Y-%m-%d %H:%M:%S'),
                'Duration': str(t.duration),
                'Profit': t.profit,
                'Pips': t.pips,
                'Strategy': t.strategy,
                'Comment': t.comment
            }
            for t in self.trades
        ]
    
    def generate_report(self) -> str:
        """สร้างรายงานแบบ text"""
        metrics = self.calculate_metrics()
        
        report = f"""
{'='*70}
                    PERFORMANCE ANALYTICS REPORT
{'='*70}

📊 OVERALL STATISTICS
{'─'*70}
Total Trades:           {metrics['total_trades']}
Winning Trades:         {metrics['winning_trades']} ({metrics['win_rate']:.2f}%)
Losing Trades:          {metrics['losing_trades']}

💰 PROFIT & LOSS
{'─'*70}
Total Profit:           ${metrics['total_profit']:,.2f}
Total Loss:             ${metrics['total_loss']:,.2f}
Net Profit:             ${metrics['net_profit']:,.2f}
Average Win:            ${metrics['avg_win']:,.2f}
Average Loss:           ${metrics['avg_loss']:,.2f}
Largest Win:            ${metrics['largest_win']:,.2f}
Largest Loss:           ${metrics['largest_loss']:,.2f}

📈 PERFORMANCE METRICS
{'─'*70}
Profit Factor:          {metrics['profit_factor']:.2f}
Risk/Reward Ratio:      {metrics['risk_reward_ratio']:.2f}
Expectancy:             ${metrics['expectancy']:,.2f}
Sharpe Ratio:           {metrics['sharpe_ratio']:.2f}
Sortino Ratio:          {metrics['sortino_ratio']:.2f}
ROI:                    {metrics['roi']:.2f}%

📉 RISK METRICS
{'─'*70}
Max Drawdown:           ${metrics['max_drawdown']:,.2f} ({metrics['max_drawdown_pct']:.2f}%)
Max Consecutive Wins:   {metrics['max_consecutive_wins']}
Max Consecutive Losses: {metrics['max_consecutive_losses']}

⏱️ TIME METRICS
{'─'*70}
Average Trade Duration: {metrics['avg_duration']}

💼 ACCOUNT SUMMARY
{'─'*70}
Initial Balance:        ${metrics['initial_balance']:,.2f}
Final Balance:          ${metrics['final_balance']:,.2f}

🎯 STRATEGY BREAKDOWN
{'─'*70}
"""
        
        for strategy, profit in metrics['profit_by_strategy'].items():
            winrate = metrics['winrate_by_strategy'].get(strategy, 0)
            report += f"{strategy:25} | Profit: ${profit:10,.2f} | Win Rate: {winrate:5.1f}%\n"
        
        report += f"\n{'='*70}\n"
        
        return report
