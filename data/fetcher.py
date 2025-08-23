import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional
import ta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockDataFetcher:
    def __init__(self):
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(minutes=5)
    
    def get_stock_data(self, symbol: str, period: str = '2y') -> pd.DataFrame:
        """Fetch stock data with caching"""
        cache_key = f"{symbol}_{period}"
        current_time = datetime.now()
        
        # Check cache
        if (cache_key in self.cache and 
            cache_key in self.cache_expiry and 
            current_time < self.cache_expiry[cache_key]):
            logger.info(f"Using cached data for {symbol}")
            return self.cache[cache_key]
        
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if data.empty:
                logger.error(f"No data found for {symbol}")
                return pd.DataFrame()
            
            # Add technical indicators
            data = self._add_technical_indicators(data)
            
            # Cache the data
            self.cache[cache_key] = data
            self.cache_expiry[cache_key] = current_time + self.cache_duration
            
            logger.info(f"Fetched fresh data for {symbol}: {len(data)} records")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to the data"""
        try:
            # Moving averages
            data['SMA_20'] = ta.trend.sma_indicator(data['Close'], window=20)
            data['SMA_50'] = ta.trend.sma_indicator(data['Close'], window=50)
            data['EMA_12'] = ta.trend.ema_indicator(data['Close'], window=12)
            data['EMA_26'] = ta.trend.ema_indicator(data['Close'], window=26)
            
            # RSI
            data['RSI'] = ta.momentum.rsi(data['Close'], window=14)
            
            # MACD
            macd = ta.trend.MACD(data['Close'])
            data['MACD'] = macd.macd()
            data['MACD_Signal'] = macd.macd_signal()
            data['MACD_Histogram'] = macd.macd_diff()
            
            # Bollinger Bands
            bollinger = ta.volatility.BollingerBands(data['Close'])
            data['BB_Upper'] = bollinger.bollinger_hband()
            data['BB_Lower'] = bollinger.bollinger_lband()
            data['BB_Middle'] = bollinger.bollinger_mavg()
            
            # Volume indicators
            data['Volume_SMA'] = data['Volume'].rolling(window=20).mean()
            
            # Price changes
            data['Price_Change'] = data['Close'].pct_change()
            data['Price_Change_5d'] = data['Close'].pct_change(periods=5)
            
            # Volatility
            data['Volatility'] = data['Price_Change'].rolling(window=20).std()
            
            return data
            
        except Exception as e:
            logger.error(f"Error adding technical indicators: {str(e)}")
            return data
    
    def get_multiple_stocks(self, symbols: List[str], period: str = '2y') -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple stocks"""
        results = {}
        for symbol in symbols:
            data = self.get_stock_data(symbol, period)
            if not data.empty:
                results[symbol] = data
        return results
    
    def get_market_info(self, symbol: str) -> Dict:
        """Get additional market information for a stock"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'peg_ratio': info.get('pegRatio'),
                'price_to_book': info.get('priceToBook'),
                'dividend_yield': info.get('dividendYield'),
                'beta': info.get('beta'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                '52_week_high': info.get('fiftyTwoWeekHigh'),
                '52_week_low': info.get('fiftyTwoWeekLow'),
                'avg_volume': info.get('averageVolume'),
                'current_price': info.get('currentPrice')
            }
        except Exception as e:
            logger.error(f"Error fetching market info for {symbol}: {str(e)}")
            return {}
    
    def get_news_sentiment(self, symbol: str) -> List[Dict]:
        """Get recent news for sentiment analysis"""
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            formatted_news = []
            for item in news[:10]:  # Get last 10 news items
                formatted_news.append({
                    'title': item.get('title', ''),
                    'summary': item.get('summary', ''),
                    'published': item.get('providerPublishTime'),
                    'publisher': item.get('publisher', ''),
                    'link': item.get('link', '')
                })
            
            return formatted_news
            
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {str(e)}")
            return []
    
    def get_market_context(self) -> Dict:
        """Get broader market context for geopolitical analysis"""
        try:
            # Get major market indices for context
            indices = {
                'SPY': 'S&P 500',
                'QQQ': 'NASDAQ',
                'DIA': 'Dow Jones',
                'VIX': 'Volatility Index',
                'GLD': 'Gold',
                'TLT': 'Treasury Bonds',
                'DXY': 'US Dollar Index'
            }
            
            market_data = {}
            for symbol, name in indices.items():
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period='5d')
                    if not hist.empty:
                        current = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
                        change_pct = ((current - prev) / prev) * 100
                        
                        market_data[symbol] = {
                            'name': name,
                            'price': current,
                            'change_pct': change_pct,
                            'volatility': hist['Close'].pct_change().std() * (252**0.5)
                        }
                except Exception as e:
                    logger.warning(f"Could not fetch data for {symbol}: {str(e)}")
            
            return {
                'market_indices': market_data,
                'timestamp': datetime.now().isoformat(),
                'market_sentiment': self._assess_market_sentiment(market_data)
            }
            
        except Exception as e:
            logger.error(f"Error fetching market context: {str(e)}")
            return {}
    
    def _assess_market_sentiment(self, market_data: Dict) -> str:
        """Assess overall market sentiment from indices"""
        try:
            if not market_data:
                return 'NEUTRAL'
            
            # Simple sentiment based on major indices
            spy_change = market_data.get('SPY', {}).get('change_pct', 0)
            vix_change = market_data.get('VIX', {}).get('change_pct', 0)
            
            if spy_change > 1 and vix_change < -5:
                return 'BULLISH'
            elif spy_change < -1 and vix_change > 5:
                return 'BEARISH'
            else:
                return 'NEUTRAL'
                
        except Exception:
            return 'NEUTRAL'
