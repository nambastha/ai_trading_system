import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class PortfolioTracker:
    def __init__(self, portfolio_file: str = "portfolio.json"):
        self.portfolio_file = portfolio_file
        self.portfolio = self._load_portfolio()
        self.trades_history = []
        
    def _load_portfolio(self) -> Dict:
        """Load portfolio from file or create new one"""
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading portfolio: {str(e)}")
        
        # Default portfolio structure
        return {
            'cash': 100000.0,  # Starting with $100k
            'positions': {},
            'trades': [],
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
    
    def _save_portfolio(self):
        """Save portfolio to file"""
        try:
            self.portfolio['last_updated'] = datetime.now().isoformat()
            with open(self.portfolio_file, 'w') as f:
                json.dump(self.portfolio, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving portfolio: {str(e)}")
    
    def execute_trade(self, symbol: str, action: str, shares: int, price: float, 
                     reasoning: str = "", confidence: float = 0.0) -> Dict:
        """Execute a trade and update portfolio"""
        trade_value = shares * price
        commission = max(1.0, trade_value * 0.001)  # 0.1% commission, min $1
        
        trade_record = {
            'symbol': symbol,
            'action': action.upper(),
            'shares': shares,
            'price': price,
            'value': trade_value,
            'commission': commission,
            'reasoning': reasoning,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        }
        
        if action.upper() == 'BUY':
            total_cost = trade_value + commission
            
            if self.portfolio['cash'] < total_cost:
                return {
                    'success': False,
                    'message': f"Insufficient funds. Need ${total_cost:.2f}, have ${self.portfolio['cash']:.2f}",
                    'trade': trade_record
                }
            
            # Update cash
            self.portfolio['cash'] -= total_cost
            
            # Update position
            if symbol in self.portfolio['positions']:
                current_shares = self.portfolio['positions'][symbol]['shares']
                current_avg_price = self.portfolio['positions'][symbol]['avg_price']
                
                new_shares = current_shares + shares
                new_avg_price = ((current_shares * current_avg_price) + trade_value) / new_shares
                
                self.portfolio['positions'][symbol] = {
                    'shares': new_shares,
                    'avg_price': new_avg_price,
                    'last_updated': datetime.now().isoformat()
                }
            else:
                self.portfolio['positions'][symbol] = {
                    'shares': shares,
                    'avg_price': price,
                    'last_updated': datetime.now().isoformat()
                }
        
        elif action.upper() == 'SELL':
            if symbol not in self.portfolio['positions']:
                return {
                    'success': False,
                    'message': f"No position in {symbol} to sell",
                    'trade': trade_record
                }
            
            current_shares = self.portfolio['positions'][symbol]['shares']
            if current_shares < shares:
                return {
                    'success': False,
                    'message': f"Insufficient shares. Trying to sell {shares}, have {current_shares}",
                    'trade': trade_record
                }
            
            # Update cash
            proceeds = trade_value - commission
            self.portfolio['cash'] += proceeds
            
            # Update position
            remaining_shares = current_shares - shares
            if remaining_shares == 0:
                del self.portfolio['positions'][symbol]
            else:
                self.portfolio['positions'][symbol]['shares'] = remaining_shares
                self.portfolio['positions'][symbol]['last_updated'] = datetime.now().isoformat()
        
        # Record trade
        self.portfolio['trades'].append(trade_record)
        self._save_portfolio()
        
        return {
            'success': True,
            'message': f"Successfully {action.lower()}ed {shares} shares of {symbol} at ${price:.2f}",
            'trade': trade_record,
            'new_cash_balance': self.portfolio['cash']
        }
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> Dict:
        """Calculate current portfolio value"""
        cash = self.portfolio['cash']
        positions_value = 0.0
        position_details = {}
        
        for symbol, position in self.portfolio['positions'].items():
            shares = position['shares']
            avg_price = position['avg_price']
            current_price = current_prices.get(symbol, avg_price)
            
            market_value = shares * current_price
            cost_basis = shares * avg_price
            unrealized_pnl = market_value - cost_basis
            unrealized_pnl_pct = (unrealized_pnl / cost_basis) * 100 if cost_basis > 0 else 0
            
            positions_value += market_value
            position_details[symbol] = {
                'shares': shares,
                'avg_price': avg_price,
                'current_price': current_price,
                'market_value': market_value,
                'cost_basis': cost_basis,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_pct': unrealized_pnl_pct
            }
        
        total_value = cash + positions_value
        
        return {
            'cash': cash,
            'positions_value': positions_value,
            'total_value': total_value,
            'position_details': position_details,
            'cash_percentage': (cash / total_value) * 100 if total_value > 0 else 0,
            'equity_percentage': (positions_value / total_value) * 100 if total_value > 0 else 0
        }
    
    def get_performance_metrics(self, current_prices: Dict[str, float]) -> Dict:
        """Calculate portfolio performance metrics"""
        portfolio_value = self.get_portfolio_value(current_prices)
        
        # Calculate returns
        initial_value = 100000.0  # Starting portfolio value
        total_return = portfolio_value['total_value'] - initial_value
        total_return_pct = (total_return / initial_value) * 100
        
        # Calculate realized P&L from trades
        realized_pnl = self._calculate_realized_pnl()
        
        # Calculate trade statistics
        trade_stats = self._calculate_trade_statistics()
        
        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(current_prices)
        
        return {
            'total_value': portfolio_value['total_value'],
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'realized_pnl': realized_pnl,
            'unrealized_pnl': sum([pos['unrealized_pnl'] for pos in portfolio_value['position_details'].values()]),
            'trade_statistics': trade_stats,
            'risk_metrics': risk_metrics,
            'portfolio_breakdown': portfolio_value
        }
    
    def _calculate_realized_pnl(self) -> float:
        """Calculate realized profit/loss from completed trades"""
        realized_pnl = 0.0
        position_tracking = {}
        
        for trade in self.portfolio['trades']:
            symbol = trade['symbol']
            action = trade['action']
            shares = trade['shares']
            price = trade['price']
            
            if symbol not in position_tracking:
                position_tracking[symbol] = {'shares': 0, 'cost_basis': 0.0}
            
            if action == 'BUY':
                position_tracking[symbol]['cost_basis'] += shares * price
                position_tracking[symbol]['shares'] += shares
            elif action == 'SELL':
                if position_tracking[symbol]['shares'] > 0:
                    avg_cost = position_tracking[symbol]['cost_basis'] / position_tracking[symbol]['shares']
                    realized_pnl += shares * (price - avg_cost)
                    
                    # Update tracking
                    position_tracking[symbol]['cost_basis'] -= shares * avg_cost
                    position_tracking[symbol]['shares'] -= shares
        
        return realized_pnl
    
    def _calculate_trade_statistics(self) -> Dict:
        """Calculate trading statistics"""
        if not self.portfolio['trades']:
            return {}
        
        trades = self.portfolio['trades']
        
        # Count trades by type
        buy_trades = [t for t in trades if t['action'] == 'BUY']
        sell_trades = [t for t in trades if t['action'] == 'SELL']
        
        # Calculate average confidence
        avg_confidence = np.mean([t.get('confidence', 0) for t in trades])
        
        # Calculate trading frequency
        if len(trades) > 1:
            first_trade = datetime.fromisoformat(trades[0]['timestamp'])
            last_trade = datetime.fromisoformat(trades[-1]['timestamp'])
            days_active = (last_trade - first_trade).days
            trades_per_day = len(trades) / max(days_active, 1)
        else:
            trades_per_day = 0
        
        return {
            'total_trades': len(trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'avg_confidence': avg_confidence,
            'trades_per_day': trades_per_day,
            'total_commissions': sum([t.get('commission', 0) for t in trades])
        }
    
    def _calculate_risk_metrics(self, current_prices: Dict[str, float]) -> Dict:
        """Calculate portfolio risk metrics"""
        portfolio_value = self.get_portfolio_value(current_prices)
        
        if not portfolio_value['position_details']:
            return {'diversification_score': 1.0, 'concentration_risk': 0.0}
        
        # Calculate concentration risk
        position_weights = []
        for pos in portfolio_value['position_details'].values():
            weight = pos['market_value'] / portfolio_value['total_value']
            position_weights.append(weight)
        
        # Herfindahl-Hirschman Index for concentration
        hhi = sum([w**2 for w in position_weights])
        diversification_score = 1 - hhi
        
        # Largest position weight
        max_position_weight = max(position_weights) if position_weights else 0
        
        return {
            'diversification_score': diversification_score,
            'concentration_risk': hhi,
            'max_position_weight': max_position_weight,
            'number_of_positions': len(portfolio_value['position_details']),
            'cash_ratio': portfolio_value['cash_percentage'] / 100
        }
    
    def get_trade_recommendations(self, analysis_results: Dict[str, Dict], 
                                max_position_size: float = 0.1) -> List[Dict]:
        """Generate trade recommendations based on analysis and current portfolio"""
        recommendations = []
        portfolio_value = self.get_portfolio_value({})
        
        for symbol, analysis in analysis_results.items():
            recommendation = analysis.get('final_recommendation', {})
            action = recommendation.get('final_recommendation', 'HOLD')
            confidence = recommendation.get('overall_confidence', 0.0)
            current_price = analysis.get('current_price', 0)
            
            if action in ['BUY', 'STRONG_BUY'] and confidence > 0.7:
                # Calculate position size
                max_investment = portfolio_value['total_value'] * max_position_size
                available_cash = self.portfolio['cash']
                investment_amount = min(max_investment, available_cash * 0.8)  # Use 80% of available cash max
                
                if investment_amount > 1000 and current_price > 0:  # Minimum $1000 investment
                    shares = int(investment_amount / current_price)
                    
                    recommendations.append({
                        'symbol': symbol,
                        'action': 'BUY',
                        'shares': shares,
                        'price': current_price,
                        'investment_amount': shares * current_price,
                        'confidence': confidence,
                        'reasoning': recommendation.get('reasoning', ''),
                        'priority': confidence
                    })
            
            elif action in ['SELL', 'STRONG_SELL'] and confidence > 0.7:
                # Check if we have position to sell
                if symbol in self.portfolio['positions']:
                    current_shares = self.portfolio['positions'][symbol]['shares']
                    
                    # Sell partial or full position based on confidence
                    sell_ratio = min(1.0, confidence * 1.2)  # Higher confidence = more aggressive selling
                    shares_to_sell = int(current_shares * sell_ratio)
                    
                    if shares_to_sell > 0:
                        recommendations.append({
                            'symbol': symbol,
                            'action': 'SELL',
                            'shares': shares_to_sell,
                            'price': current_price,
                            'investment_amount': shares_to_sell * current_price,
                            'confidence': confidence,
                            'reasoning': recommendation.get('reasoning', ''),
                            'priority': confidence
                        })
        
        # Sort by priority (confidence)
        recommendations.sort(key=lambda x: x['priority'], reverse=True)
        
        return recommendations
    
    def get_portfolio_summary(self, current_prices: Dict[str, float] = None) -> Dict:
        """Get comprehensive portfolio summary"""
        if current_prices is None:
            current_prices = {}
        
        portfolio_value = self.get_portfolio_value(current_prices)
        performance = self.get_performance_metrics(current_prices)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'portfolio_value': portfolio_value,
            'performance_metrics': performance,
            'positions_count': len(self.portfolio['positions']),
            'cash_balance': self.portfolio['cash'],
            'total_trades': len(self.portfolio['trades']),
            'last_trade': self.portfolio['trades'][-1]['timestamp'] if self.portfolio['trades'] else None
        }
