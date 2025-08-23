import openai
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
from config import Config

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    def __init__(self):
        self.client = None
        if Config.OPENAI_API_KEY and Config.OPENAI_API_KEY != 'your_openai_api_key_here':
            try:
                self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {str(e)}")
        else:
            logger.warning("OpenAI API key not configured - using demo mode")
        
    def analyze_market_sentiment(self, news_data: List[Dict], stock_symbol: str) -> Dict:
        """Analyze market sentiment using LLM"""
        if not news_data:
            return {'sentiment': 'NEUTRAL', 'confidence': 0.5, 'reasoning': 'No news data available'}
        
        # If no OpenAI client, use demo mode
        if not self.client:
            return self._demo_sentiment_analysis(news_data, stock_symbol)
        
        # Prepare news summary for LLM
        news_summary = self._prepare_news_summary(news_data)
        
        prompt = f"""
        Analyze the market sentiment for {stock_symbol} based on the following recent news:

        {news_summary}

        Provide a comprehensive JSON response with:
        1. sentiment: "BULLISH", "BEARISH", or "NEUTRAL"
        2. confidence: float between 0 and 1
        3. reasoning: detailed explanation including geopolitical factors
        4. key_factors: list of main factors influencing sentiment
        5. risk_level: "LOW", "MEDIUM", or "HIGH"
        6. geopolitical_impact: assessment of geopolitical risks/opportunities
        7. economic_environment: analysis of broader economic conditions
        8. sector_outlook: industry-specific trends and challenges

        Consider ALL of the following factors:
        
        **Company Fundamentals:**
        - Earnings reports, guidance, and financial health
        - Management commentary and strategic initiatives
        - Competitive positioning and market share

        **Geopolitical Factors:**
        - Trade tensions, tariffs, and international relations
        - Regulatory changes and government policies
        - Currency fluctuations and their impact on operations
        - Supply chain disruptions from global events
        - Sanctions, political instability, and regional conflicts
        - Energy prices and commodity market impacts

        **Economic Environment:**
        - Interest rate environment and monetary policy
        - Inflation trends and consumer spending patterns
        - Employment data and economic growth indicators
        - Market liquidity and investor sentiment

        **Industry & Sector Analysis:**
        - Technological disruptions and innovation cycles
        - Regulatory changes specific to the industry
        - Competitive landscape and market dynamics
        - ESG considerations and sustainability trends
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a senior geopolitical and financial analyst with expertise in global markets, international relations, and macroeconomic trends. Provide comprehensive, nuanced analysis that considers both financial and geopolitical factors."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Error in LLM sentiment analysis: {str(e)}")
            return {'sentiment': 'NEUTRAL', 'confidence': 0.5, 'reasoning': f'Analysis error: {str(e)}'}
    
    def analyze_technical_patterns(self, stock_data: pd.DataFrame, symbol: str) -> Dict:
        """Analyze technical patterns using LLM"""
        # If no OpenAI client, use demo mode
        if not self.client:
            return self._demo_technical_analysis(stock_data, symbol)
        
        # Prepare technical data summary
        latest_data = stock_data.tail(20)  # Last 20 days
        
        technical_summary = self._prepare_technical_summary(latest_data, symbol)
        
        prompt = f"""
        Analyze the technical patterns for {symbol} based on the following data:

        {technical_summary}

        Provide a JSON response with:
        1. pattern_detected: name of detected pattern or "NONE"
        2. signal: "BUY", "SELL", or "HOLD"
        3. confidence: float between 0 and 1
        4. reasoning: detailed technical analysis
        5. support_level: estimated support price
        6. resistance_level: estimated resistance price
        7. target_price: potential target price
        8. stop_loss: recommended stop loss level

        Focus on:
        - Chart patterns (triangles, flags, head & shoulders, etc.)
        - Moving average crossovers
        - RSI levels and divergences
        - MACD signals
        - Volume analysis
        - Bollinger Band position
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert technical analyst with deep knowledge of chart patterns and indicators."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=600
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Error in LLM technical analysis: {str(e)}")
            return {'signal': 'HOLD', 'confidence': 0.5, 'reasoning': f'Analysis error: {str(e)}'}
    
    def generate_trading_recommendation(self, 
                                      markov_signal: Dict, 
                                      sentiment_analysis: Dict, 
                                      technical_analysis: Dict,
                                      market_info: Dict,
                                      symbol: str) -> Dict:
        """Generate final trading recommendation combining all analyses"""
        
        # If no OpenAI client, use demo mode
        if not self.client:
            return self._demo_trading_recommendation(markov_signal, sentiment_analysis, technical_analysis, market_info, symbol)
        
        analysis_summary = {
            'markov_chain': markov_signal,
            'sentiment': sentiment_analysis,
            'technical': technical_analysis,
            'market_info': market_info
        }
        
        prompt = f"""
        Generate a comprehensive trading recommendation for {symbol} based on the following analyses:

        MARKOV CHAIN ANALYSIS:
        - Signal: {markov_signal.get('signal', 'N/A')}
        - Confidence: {markov_signal.get('confidence', 0)}
        - Reasoning: {markov_signal.get('reason', 'N/A')}

        SENTIMENT ANALYSIS:
        - Sentiment: {sentiment_analysis.get('sentiment', 'N/A')}
        - Confidence: {sentiment_analysis.get('confidence', 0)}
        - Key Factors: {sentiment_analysis.get('key_factors', [])}
        - Geopolitical Impact: {sentiment_analysis.get('geopolitical_impact', 'N/A')}
        - Economic Environment: {sentiment_analysis.get('economic_environment', 'N/A')}
        - Sector Outlook: {sentiment_analysis.get('sector_outlook', 'N/A')}

        TECHNICAL ANALYSIS:
        - Signal: {technical_analysis.get('signal', 'N/A')}
        - Pattern: {technical_analysis.get('pattern_detected', 'N/A')}
        - Confidence: {technical_analysis.get('confidence', 0)}

        MARKET INFO:
        - Current Price: ${market_info.get('current_price', 'N/A')}
        - PE Ratio: {market_info.get('pe_ratio', 'N/A')}
        - Beta: {market_info.get('beta', 'N/A')}
        - 52W High: ${market_info.get('52_week_high', 'N/A')}
        - 52W Low: ${market_info.get('52_week_low', 'N/A')}
        - Sector: {market_info.get('sector', 'N/A')}
        - Market Cap: {market_info.get('market_cap', 'N/A')}

        As a senior portfolio manager with expertise in geopolitical risk assessment, provide a JSON response with:
        
        1. final_recommendation: "STRONG_BUY", "BUY", "HOLD", "SELL", or "STRONG_SELL"
        2. overall_confidence: float between 0 and 1
        3. reasoning: comprehensive explanation integrating all factors
        4. risk_assessment: "LOW", "MEDIUM", or "HIGH"
        5. time_horizon: "SHORT_TERM", "MEDIUM_TERM", or "LONG_TERM"
        6. entry_price: recommended entry price
        7. stop_loss: recommended stop loss
        8. take_profit: recommended take profit levels
        9. position_size: recommended position size as percentage of portfolio
        10. key_risks: list of main risks including geopolitical
        11. catalysts: potential positive catalysts
        12. geopolitical_considerations: specific geopolitical factors affecting this stock
        13. macroeconomic_factors: broader economic trends impacting the investment
        14. sector_specific_risks: industry-related risks and opportunities
        15. currency_exposure: impact of currency fluctuations if applicable
        16. regulatory_environment: current and potential regulatory changes
        17. supply_chain_risks: geopolitical supply chain considerations

        Consider the current global environment including:
        - US-China trade relations and technology tensions
        - European energy security and Russia-Ukraine conflict impacts
        - Middle East geopolitical stability and oil markets
        - Central bank policies and interest rate environments
        - Inflation trends and currency volatility
        - Emerging market stability and capital flows
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a senior portfolio manager and geopolitical risk analyst with 20+ years of experience in global markets. Provide comprehensive, balanced recommendations that integrate financial analysis with geopolitical and macroeconomic considerations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1200
            )
            
            result = json.loads(response.choices[0].message.content)
            result['timestamp'] = datetime.now().isoformat()
            result['symbol'] = symbol
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating trading recommendation: {str(e)}")
            return {
                'final_recommendation': 'HOLD',
                'overall_confidence': 0.5,
                'reasoning': f'Unable to generate recommendation due to error: {str(e)}',
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol
            }
    
    def _prepare_news_summary(self, news_data: List[Dict]) -> str:
        """Prepare news data for LLM analysis"""
        summary = ""
        for i, news in enumerate(news_data[:5], 1):  # Top 5 news items
            title = news.get('title', 'No title')
            summary_text = news.get('summary', 'No summary')
            publisher = news.get('publisher', 'Unknown')
            
            summary += f"{i}. {title}\n"
            summary += f"   Source: {publisher}\n"
            summary += f"   Summary: {summary_text[:200]}...\n\n"
        
        return summary
    
    def _prepare_technical_summary(self, data: pd.DataFrame, symbol: str) -> str:
        """Prepare technical data for LLM analysis"""
        if data.empty:
            return "No technical data available"
        
        latest = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else latest
        
        summary = f"""
        CURRENT LEVELS ({symbol}):
        - Price: ${latest['Close']:.2f} (Change: {((latest['Close'] - prev['Close']) / prev['Close'] * 100):+.2f}%)
        - Volume: {latest['Volume']:,} (Avg: {data['Volume'].mean():,.0f})
        
        MOVING AVERAGES:
        - SMA 20: ${latest.get('SMA_20', 0):.2f}
        - SMA 50: ${latest.get('SMA_50', 0):.2f}
        - EMA 12: ${latest.get('EMA_12', 0):.2f}
        - EMA 26: ${latest.get('EMA_26', 0):.2f}
        
        MOMENTUM INDICATORS:
        - RSI: {latest.get('RSI', 0):.1f}
        - MACD: {latest.get('MACD', 0):.3f}
        - MACD Signal: {latest.get('MACD_Signal', 0):.3f}
        
        BOLLINGER BANDS:
        - Upper: ${latest.get('BB_Upper', 0):.2f}
        - Middle: ${latest.get('BB_Middle', 0):.2f}
        - Lower: ${latest.get('BB_Lower', 0):.2f}
        
        VOLATILITY:
        - 20-day volatility: {latest.get('Volatility', 0):.3f}
        
        RECENT PRICE ACTION:
        - 5-day change: {latest.get('Price_Change_5d', 0)*100:+.2f}%
        - High: ${data['High'].tail(20).max():.2f}
        - Low: ${data['Low'].tail(20).min():.2f}
        """
        
        return summary
    
    def _demo_sentiment_analysis(self, news_data: List[Dict], symbol: str) -> Dict:
        """Demo sentiment analysis without OpenAI API"""
        # Simple keyword-based sentiment analysis
        positive_keywords = ['growth', 'profit', 'beat', 'strong', 'positive', 'up', 'gain', 'bullish']
        negative_keywords = ['loss', 'decline', 'weak', 'negative', 'down', 'fall', 'bearish', 'concern']
        
        positive_count = 0
        negative_count = 0
        
        for news in news_data[:5]:
            title = news.get('title', '').lower()
            summary = news.get('summary', '').lower()
            text = title + ' ' + summary
            
            positive_count += sum(1 for word in positive_keywords if word in text)
            negative_count += sum(1 for word in negative_keywords if word in text)
        
        if positive_count > negative_count:
            sentiment = 'BULLISH'
            confidence = min(0.8, 0.5 + (positive_count - negative_count) * 0.1)
        elif negative_count > positive_count:
            sentiment = 'BEARISH'
            confidence = min(0.8, 0.5 + (negative_count - positive_count) * 0.1)
        else:
            sentiment = 'NEUTRAL'
            confidence = 0.5
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'reasoning': f'Demo analysis based on keyword sentiment (pos: {positive_count}, neg: {negative_count})',
            'key_factors': ['Demo mode - keyword analysis only'],
            'risk_level': 'MEDIUM'
        }
    
    def _demo_technical_analysis(self, stock_data: pd.DataFrame, symbol: str) -> Dict:
        """Demo technical analysis without OpenAI API"""
        if stock_data.empty:
            return {'signal': 'HOLD', 'confidence': 0.5, 'reasoning': 'No data available'}
        
        latest = stock_data.iloc[-1]
        current_price = latest['Close']
        
        # Simple technical analysis
        signal = 'HOLD'
        confidence = 0.6
        reasoning = 'Demo technical analysis: '
        
        # RSI analysis
        rsi = latest.get('RSI', 50)
        if rsi < 30:
            signal = 'BUY'
            reasoning += f'RSI oversold ({rsi:.1f}). '
        elif rsi > 70:
            signal = 'SELL'
            reasoning += f'RSI overbought ({rsi:.1f}). '
        
        # Moving average analysis
        sma_20 = latest.get('SMA_20', current_price)
        if current_price > sma_20 * 1.02:
            if signal != 'SELL':
                signal = 'BUY'
            reasoning += f'Price above SMA20 ({current_price:.2f} > {sma_20:.2f}). '
        elif current_price < sma_20 * 0.98:
            if signal != 'BUY':
                signal = 'SELL'
            reasoning += f'Price below SMA20 ({current_price:.2f} < {sma_20:.2f}). '
        
        return {
            'pattern_detected': 'Demo Analysis',
            'signal': signal,
            'confidence': confidence,
            'reasoning': reasoning + '(Demo mode - simplified analysis)',
            'support_level': current_price * 0.95,
            'resistance_level': current_price * 1.05,
            'target_price': current_price * 1.1 if signal == 'BUY' else current_price * 0.9,
            'stop_loss': current_price * 0.95 if signal == 'BUY' else current_price * 1.05
        }
    
    def _demo_trading_recommendation(self, markov_signal: Dict, sentiment_analysis: Dict, 
                                   technical_analysis: Dict, market_info: Dict, symbol: str) -> Dict:
        """Demo trading recommendation without OpenAI API"""
        # Combine signals with simple logic
        signals = []
        confidences = []
        
        # Markov signal
        markov_rec = markov_signal.get('signal', 'HOLD')
        if markov_rec in ['BUY', 'STRONG_BUY']:
            signals.append(1)
        elif markov_rec in ['SELL', 'STRONG_SELL']:
            signals.append(-1)
        else:
            signals.append(0)
        confidences.append(markov_signal.get('confidence', 0.5))
        
        # Sentiment signal
        sentiment = sentiment_analysis.get('sentiment', 'NEUTRAL')
        if sentiment == 'BULLISH':
            signals.append(1)
        elif sentiment == 'BEARISH':
            signals.append(-1)
        else:
            signals.append(0)
        confidences.append(sentiment_analysis.get('confidence', 0.5))
        
        # Technical signal
        tech_signal = technical_analysis.get('signal', 'HOLD')
        if tech_signal == 'BUY':
            signals.append(1)
        elif tech_signal == 'SELL':
            signals.append(-1)
        else:
            signals.append(0)
        confidences.append(technical_analysis.get('confidence', 0.5))
        
        # Calculate final recommendation
        avg_signal = sum(signals) / len(signals)
        avg_confidence = sum(confidences) / len(confidences)
        
        if avg_signal > 0.3:
            final_rec = 'BUY' if avg_signal > 0.6 else 'BUY'
        elif avg_signal < -0.3:
            final_rec = 'SELL' if avg_signal < -0.6 else 'SELL'
        else:
            final_rec = 'HOLD'
        
        current_price = market_info.get('current_price', 100)
        
        return {
            'final_recommendation': final_rec,
            'overall_confidence': min(0.8, avg_confidence),
            'reasoning': f'Demo mode: Combined Markov ({markov_rec}), Sentiment ({sentiment}), Technical ({tech_signal}) analysis',
            'risk_assessment': 'MEDIUM',
            'time_horizon': 'MEDIUM_TERM',
            'entry_price': current_price,
            'stop_loss': current_price * 0.95 if final_rec == 'BUY' else current_price * 1.05,
            'take_profit': current_price * 1.1 if final_rec == 'BUY' else current_price * 0.9,
            'position_size': 5.0,  # 5% position size
            'key_risks': ['Demo mode - simplified analysis', 'Market volatility'],
            'catalysts': ['Technical indicators', 'Market sentiment'],
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol
        }
