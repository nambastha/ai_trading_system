import logging
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
from data_fetcher import StockDataFetcher
from markov_analyzer import MarkovChainAnalyzer
from llm_analyzer import LLMAnalyzer
from config import Config

logger = logging.getLogger(__name__)

class TradingEngine:
    def __init__(self):
        self.data_fetcher = StockDataFetcher()
        self.markov_analyzer = MarkovChainAnalyzer(n_states=Config.MARKOV_STATES)
        self.llm_analyzer = LLMAnalyzer()
        self.analysis_cache = {}
        
    def analyze_stock(self, symbol: str) -> Dict:
        """Comprehensive stock analysis combining all methods"""
        logger.info(f"Starting comprehensive analysis for {symbol}")
        
        try:
            # 1. Fetch stock data
            stock_data = self.data_fetcher.get_stock_data(symbol, Config.HISTORICAL_DATA_PERIOD)
            if stock_data.empty:
                return self._create_error_result(symbol, "Unable to fetch stock data")
            
            # 2. Get market information
            market_info = self.data_fetcher.get_market_info(symbol)
            
            # 3. Get news for sentiment analysis
            news_data = self.data_fetcher.get_news_sentiment(symbol)
            
            # 4. Markov Chain Analysis
            logger.info(f"Running Markov chain analysis for {symbol}")
            self.markov_analyzer.build_transition_matrix(stock_data)
            markov_signal = self.markov_analyzer.get_trading_signal(Config.BUY_CONFIDENCE_THRESHOLD)
            markov_outlook = self.markov_analyzer.get_long_term_outlook()
            pattern_strength = self.markov_analyzer.analyze_pattern_strength()
            
            # 5. LLM Sentiment Analysis
            logger.info(f"Running sentiment analysis for {symbol}")
            sentiment_analysis = self.llm_analyzer.analyze_market_sentiment(news_data, symbol)
            
            # 6. LLM Technical Analysis
            logger.info(f"Running technical analysis for {symbol}")
            technical_analysis = self.llm_analyzer.analyze_technical_patterns(stock_data, symbol)
            
            # 7. Generate Final Recommendation
            logger.info(f"Generating final recommendation for {symbol}")
            final_recommendation = self.llm_analyzer.generate_trading_recommendation(
                markov_signal, sentiment_analysis, technical_analysis, market_info, symbol
            )
            
            # 8. Compile comprehensive result
            result = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'current_price': market_info.get('current_price'),
                'markov_analysis': {
                    'signal': markov_signal,
                    'long_term_outlook': markov_outlook,
                    'pattern_strength': pattern_strength
                },
                'sentiment_analysis': sentiment_analysis,
                'technical_analysis': technical_analysis,
                'market_info': market_info,
                'final_recommendation': final_recommendation,
                'risk_metrics': self._calculate_risk_metrics(stock_data, market_info),
                'data_quality': self._assess_data_quality(stock_data, news_data)
            }
            
            # Cache the result
            self.analysis_cache[symbol] = result
            
            logger.info(f"Completed analysis for {symbol}: {final_recommendation.get('final_recommendation')}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {str(e)}")
            return self._create_error_result(symbol, str(e))
    
    def get_trading_signals(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get trading signals for multiple stocks"""
        signals = {}
        
        for symbol in symbols:
            try:
                analysis = self.analyze_stock(symbol)
                signals[symbol] = {
                    'recommendation': analysis['final_recommendation']['final_recommendation'],
                    'confidence': analysis['final_recommendation']['overall_confidence'],
                    'current_price': analysis['current_price'],
                    'reasoning': analysis['final_recommendation']['reasoning'],
                    'risk_level': analysis['final_recommendation'].get('risk_assessment', 'MEDIUM'),
                    'timestamp': analysis['timestamp']
                }
            except Exception as e:
                logger.error(f"Error getting signal for {symbol}: {str(e)}")
                signals[symbol] = {
                    'recommendation': 'HOLD',
                    'confidence': 0.0,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        
        return signals
    
    def screen_for_opportunities(self, symbols: List[str], min_confidence: float = 0.7) -> List[Dict]:
        """Screen stocks for high-confidence trading opportunities"""
        opportunities = []
        
        signals = self.get_trading_signals(symbols)
        
        for symbol, signal in signals.items():
            if signal.get('confidence', 0) >= min_confidence:
                if signal['recommendation'] in ['STRONG_BUY', 'BUY', 'STRONG_SELL', 'SELL']:
                    opportunities.append({
                        'symbol': symbol,
                        'action': signal['recommendation'],
                        'confidence': signal['confidence'],
                        'current_price': signal.get('current_price'),
                        'reasoning': signal.get('reasoning', ''),
                        'risk_level': signal.get('risk_level', 'MEDIUM'),
                        'timestamp': signal['timestamp']
                    })
        
        # Sort by confidence
        opportunities.sort(key=lambda x: x['confidence'], reverse=True)
        
        return opportunities
    
    def _calculate_risk_metrics(self, stock_data: pd.DataFrame, market_info: Dict) -> Dict:
        """Calculate risk metrics for the stock"""
        if stock_data.empty:
            return {}
        
        try:
            returns = stock_data['Close'].pct_change().dropna()
            
            # Calculate various risk metrics
            volatility = returns.std() * (252 ** 0.5)  # Annualized volatility
            var_95 = returns.quantile(0.05)  # Value at Risk (95%)
            max_drawdown = self._calculate_max_drawdown(stock_data['Close'])
            
            # Sharpe ratio approximation (assuming risk-free rate of 2%)
            excess_returns = returns.mean() * 252 - 0.02
            sharpe_ratio = excess_returns / volatility if volatility > 0 else 0
            
            return {
                'volatility': volatility,
                'var_95': var_95,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'beta': market_info.get('beta', 1.0),
                'avg_volume': market_info.get('avg_volume', 0)
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {str(e)}")
            return {}
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown"""
        try:
            peak = prices.expanding().max()
            drawdown = (prices - peak) / peak
            return drawdown.min()
        except:
            return 0.0
    
    def _assess_data_quality(self, stock_data: pd.DataFrame, news_data: List[Dict]) -> Dict:
        """Assess the quality of data used in analysis"""
        return {
            'stock_data_points': len(stock_data),
            'stock_data_completeness': 1.0 - (stock_data.isnull().sum().sum() / (len(stock_data) * len(stock_data.columns))),
            'news_articles_count': len(news_data),
            'data_freshness_hours': (datetime.now() - stock_data.index[-1].replace(tzinfo=None)).total_seconds() / 3600 if not stock_data.empty else 999,
            'quality_score': self._calculate_quality_score(stock_data, news_data)
        }
    
    def _calculate_quality_score(self, stock_data: pd.DataFrame, news_data: List[Dict]) -> float:
        """Calculate overall data quality score"""
        score = 0.0
        
        # Stock data quality (40% weight)
        if not stock_data.empty:
            completeness = 1.0 - (stock_data.isnull().sum().sum() / (len(stock_data) * len(stock_data.columns)))
            recency = max(0, 1.0 - ((datetime.now() - stock_data.index[-1].replace(tzinfo=None)).total_seconds() / (24 * 3600)))
            score += 0.4 * (completeness * 0.7 + recency * 0.3)
        
        # News data quality (30% weight)
        news_score = min(1.0, len(news_data) / 10.0)  # Optimal around 10 news articles
        score += 0.3 * news_score
        
        # Volume and liquidity (30% weight)
        if not stock_data.empty and 'Volume' in stock_data.columns:
            avg_volume = stock_data['Volume'].mean()
            volume_score = min(1.0, avg_volume / 1000000)  # Good liquidity above 1M shares
            score += 0.3 * volume_score
        
        return min(1.0, score)
    
    def _create_error_result(self, symbol: str, error_message: str) -> Dict:
        """Create standardized error result"""
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'error': error_message,
            'final_recommendation': {
                'final_recommendation': 'HOLD',
                'overall_confidence': 0.0,
                'reasoning': f'Analysis failed: {error_message}',
                'risk_assessment': 'HIGH'
            }
        }
