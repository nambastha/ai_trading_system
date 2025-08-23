#!/usr/bin/env python3
"""
AI-Powered Stock Trading System
Combines Markov Chain analysis with LLM insights for intelligent trading decisions
"""

import logging
import schedule
import time
import argparse
from datetime import datetime
from typing import List
import json

from config import Config
from trading.engine import TradingEngine
from utils.alerts import AlertSystem
from trading.portfolio import PortfolioTracker
from data.fetcher import StockDataFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AITradingSystem:
    def __init__(self):
        self.trading_engine = TradingEngine()
        self.alert_system = AlertSystem()
        self.portfolio_tracker = PortfolioTracker()
        self.data_fetcher = StockDataFetcher()
        
        logger.info("AI Trading System initialized successfully")
    
    def run_analysis(self, symbols: List[str] = None) -> None:
        """Run comprehensive analysis on specified stocks"""
        if symbols is None:
            symbols = Config.DEFAULT_STOCKS
        
        logger.info(f"Starting analysis for {len(symbols)} stocks: {symbols}")
        
        try:
            # Screen for opportunities
            opportunities = self.trading_engine.screen_for_opportunities(
                symbols, 
                min_confidence=Config.BUY_CONFIDENCE_THRESHOLD
            )
            
            if opportunities:
                logger.info(f"Found {len(opportunities)} trading opportunities")
                
                # Send opportunity alerts
                self.alert_system.send_opportunity_alerts(opportunities)
                
                # Get current prices for portfolio valuation
                current_prices = {}
                for symbol in symbols:
                    data = self.data_fetcher.get_stock_data(symbol, '1d')
                    if not data.empty:
                        current_prices[symbol] = data['Close'].iloc[-1]
                
                # Generate trade recommendations
                analysis_results = {}
                for opp in opportunities:
                    symbol = opp['symbol']
                    analysis_results[symbol] = self.trading_engine.analyze_stock(symbol)
                
                trade_recommendations = self.portfolio_tracker.get_trade_recommendations(
                    analysis_results, 
                    max_position_size=Config.MAX_POSITION_SIZE
                )
                
                if trade_recommendations:
                    logger.info(f"Generated {len(trade_recommendations)} trade recommendations")
                    self._log_trade_recommendations(trade_recommendations)
                
                # Update portfolio summary
                portfolio_summary = self.portfolio_tracker.get_portfolio_summary(current_prices)
                logger.info(f"Portfolio Value: ${portfolio_summary['portfolio_value']['total_value']:,.2f}")
                
            else:
                logger.info("No high-confidence opportunities found")
                
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
    
    def analyze_single_stock(self, symbol: str) -> None:
        """Analyze a single stock and send alert if actionable"""
        logger.info(f"Analyzing {symbol}")
        
        try:
            analysis = self.trading_engine.analyze_stock(symbol)
            
            if analysis.get('error'):
                logger.error(f"Analysis failed for {symbol}: {analysis['error']}")
                return
            
            recommendation = analysis['final_recommendation']['final_recommendation']
            confidence = analysis['final_recommendation']['overall_confidence']
            
            logger.info(f"{symbol}: {recommendation} (Confidence: {confidence:.1%})")
            
            # Send alert if high confidence and actionable
            if confidence >= Config.BUY_CONFIDENCE_THRESHOLD and recommendation != 'HOLD':
                self.alert_system.send_trading_alert(analysis, "SINGLE_STOCK_ALERT")
                logger.info(f"Alert sent for {symbol}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {str(e)}")
    
    def execute_trade(self, symbol: str, action: str, shares: int, price: float = None) -> None:
        """Execute a trade manually"""
        try:
            if price is None:
                # Get current price
                data = self.data_fetcher.get_stock_data(symbol, '1d')
                if data.empty:
                    logger.error(f"Cannot get current price for {symbol}")
                    return
                price = data['Close'].iloc[-1]
            
            result = self.portfolio_tracker.execute_trade(
                symbol, action, shares, price, 
                reasoning="Manual trade execution"
            )
            
            if result['success']:
                logger.info(f"Trade executed: {result['message']}")
                
                # Send trade confirmation alert
                trade_info = {
                    'symbol': symbol,
                    'final_recommendation': {
                        'final_recommendation': action.upper(),
                        'overall_confidence': 1.0,
                        'reasoning': f"Manual trade: {action} {shares} shares at ${price:.2f}"
                    },
                    'current_price': price
                }
                self.alert_system.send_trading_alert(trade_info, "TRADE_EXECUTED")
            else:
                logger.error(f"Trade failed: {result['message']}")
                
        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
    
    def get_portfolio_status(self) -> None:
        """Display current portfolio status"""
        try:
            # Get current prices
            current_prices = {}
            for symbol in self.portfolio_tracker.portfolio['positions'].keys():
                data = self.data_fetcher.get_stock_data(symbol, '1d')
                if not data.empty:
                    current_prices[symbol] = data['Close'].iloc[-1]
            
            summary = self.portfolio_tracker.get_portfolio_summary(current_prices)
            
            print("\n" + "="*60)
            print("PORTFOLIO SUMMARY")
            print("="*60)
            print(f"Total Value: ${summary['portfolio_value']['total_value']:,.2f}")
            print(f"Cash: ${summary['cash_balance']:,.2f}")
            print(f"Positions: {summary['positions_count']}")
            print(f"Total Trades: {summary['total_trades']}")
            
            if summary['portfolio_value']['position_details']:
                print("\nCURRENT POSITIONS:")
                print("-"*60)
                for symbol, pos in summary['portfolio_value']['position_details'].items():
                    print(f"{symbol}: {pos['shares']} shares @ ${pos['current_price']:.2f}")
                    print(f"  Value: ${pos['market_value']:,.2f} | P&L: ${pos['unrealized_pnl']:,.2f} ({pos['unrealized_pnl_pct']:+.1f}%)")
            
            performance = summary['performance_metrics']
            print(f"\nPERFORMANCE:")
            print("-"*60)
            print(f"Total Return: ${performance['total_return']:,.2f} ({performance['total_return_pct']:+.1f}%)")
            print(f"Realized P&L: ${performance['realized_pnl']:,.2f}")
            print(f"Unrealized P&L: ${performance['unrealized_pnl']:,.2f}")
            
        except Exception as e:
            logger.error(f"Error getting portfolio status: {str(e)}")
    
    def schedule_analysis(self) -> None:
        """Schedule regular analysis"""
        # Schedule analysis every 30 minutes during market hours (9:30 AM - 4:00 PM EST)
        schedule.every().day.at("09:30").do(self.run_analysis)
        schedule.every().day.at("10:00").do(self.run_analysis)
        schedule.every().day.at("10:30").do(self.run_analysis)
        schedule.every().day.at("11:00").do(self.run_analysis)
        schedule.every().day.at("11:30").do(self.run_analysis)
        schedule.every().day.at("12:00").do(self.run_analysis)
        schedule.every().day.at("12:30").do(self.run_analysis)
        schedule.every().day.at("13:00").do(self.run_analysis)
        schedule.every().day.at("13:30").do(self.run_analysis)
        schedule.every().day.at("14:00").do(self.run_analysis)
        schedule.every().day.at("14:30").do(self.run_analysis)
        schedule.every().day.at("15:00").do(self.run_analysis)
        schedule.every().day.at("15:30").do(self.run_analysis)
        schedule.every().day.at("16:00").do(self.run_analysis)
        
        logger.info("Analysis scheduled for market hours (9:30 AM - 4:00 PM EST)")
        
        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _log_trade_recommendations(self, recommendations: List[dict]) -> None:
        """Log trade recommendations"""
        print("\n" + "="*60)
        print("TRADE RECOMMENDATIONS")
        print("="*60)
        
        for i, rec in enumerate(recommendations[:5], 1):  # Top 5 recommendations
            print(f"{i}. {rec['action']} {rec['shares']} shares of {rec['symbol']}")
            print(f"   Price: ${rec['price']:.2f} | Investment: ${rec['investment_amount']:,.2f}")
            print(f"   Confidence: {rec['confidence']:.1%}")
            print(f"   Reason: {rec['reasoning'][:100]}...")
            print()

def main():
    parser = argparse.ArgumentParser(description='AI-Powered Stock Trading System')
    parser.add_argument('--mode', choices=['analyze', 'single', 'portfolio', 'trade', 'schedule'], 
                       default='analyze', help='Operation mode')
    parser.add_argument('--symbol', type=str, help='Stock symbol for single analysis or trade')
    parser.add_argument('--symbols', nargs='+', help='List of stock symbols to analyze')
    parser.add_argument('--action', choices=['BUY', 'SELL'], help='Trade action')
    parser.add_argument('--shares', type=int, help='Number of shares to trade')
    parser.add_argument('--price', type=float, help='Trade price (optional, uses current price if not specified)')
    
    args = parser.parse_args()
    
    # Initialize the trading system
    system = AITradingSystem()
    
    try:
        if args.mode == 'analyze':
            symbols = args.symbols or Config.DEFAULT_STOCKS
            system.run_analysis(symbols)
            
        elif args.mode == 'single':
            if not args.symbol:
                print("Error: --symbol required for single stock analysis")
                return
            system.analyze_single_stock(args.symbol.upper())
            
        elif args.mode == 'portfolio':
            system.get_portfolio_status()
            
        elif args.mode == 'trade':
            if not all([args.symbol, args.action, args.shares]):
                print("Error: --symbol, --action, and --shares required for trading")
                return
            system.execute_trade(args.symbol.upper(), args.action, args.shares, args.price)
            
        elif args.mode == 'schedule':
            print("Starting scheduled analysis mode...")
            print("Press Ctrl+C to stop")
            system.schedule_analysis()
            
    except KeyboardInterrupt:
        logger.info("Trading system stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()
