# AI-Powered Stock Trading System

A comprehensive stock trading system that combines **Markov Chain analysis** with **Large Language Model (LLM) insights** to generate intelligent buy/sell signals and alerts.

## 🚀 Features

- **Dual Analysis Engine**: Combines quantitative Markov chain patterns with qualitative LLM sentiment analysis
- **Real-time Alerts**: Automated buy/sell notifications via Slack and email
- **Portfolio Management**: Track positions, performance, and risk metrics
- **Technical Analysis**: 20+ technical indicators including RSI, MACD, Bollinger Bands
- **News Sentiment**: LLM-powered analysis of market news and sentiment
- **Risk Management**: Built-in stop-loss, position sizing, and risk assessment
- **Automated Screening**: Continuously scan stocks for high-confidence opportunities

## 📋 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Fetcher  │───▶│  Markov Analyzer │───▶│ Trading Engine  │
│   (yfinance)    │    │  (Patterns)      │    │  (Signals)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  News & Market  │───▶│   LLM Analyzer   │───▶│  Alert System   │
│   Information   │    │  (Sentiment)     │    │ (Slack/Email)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │Portfolio Tracker│
                       │ (Performance)   │
                       └─────────────────┘
```

## 🛠️ Installation

1. **Clone and navigate to the project:**
```bash
cd /Users/nambastha/IdeaProjects/mcp_stock_server/ai_trading_system
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

4. **Required API Keys:**
   - **OpenAI API Key**: For LLM analysis (required)
   - **Slack Bot Token**: For Slack alerts (optional)
   - **Email credentials**: For email alerts (optional)

## 🚦 Quick Start

### 1. Analyze Default Stocks
```bash
python main.py --mode analyze
```

### 2. Analyze Single Stock
```bash
python main.py --mode single --symbol AAPL
```

### 3. Check Portfolio Status
```bash
python main.py --mode portfolio
```

### 4. Execute Manual Trade
```bash
python main.py --mode trade --symbol TSLA --action BUY --shares 10
```

### 5. Start Automated Monitoring
```bash
python main.py --mode schedule
```

## 📊 Analysis Components

### Markov Chain Analysis
- **State Discretization**: Converts price movements into 5 discrete states
- **Transition Matrix**: Models probability of moving between states
- **Pattern Recognition**: Identifies recurring price patterns
- **Predictive Modeling**: Forecasts next-day price movements

### LLM Integration
- **Sentiment Analysis**: Analyzes news headlines and market sentiment
- **Technical Pattern Recognition**: Identifies chart patterns and signals
- **Risk Assessment**: Evaluates market conditions and risks
- **Final Recommendation**: Combines all analyses for actionable insights

### Technical Indicators
- Moving Averages (SMA, EMA)
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Volume Analysis
- Volatility Metrics

## 🎯 Trading Signals

The system generates signals based on:

1. **Markov Chain Confidence** (>70% threshold)
2. **LLM Sentiment Score** (Bullish/Bearish/Neutral)
3. **Technical Indicator Alignment**
4. **Risk-Reward Ratio**
5. **Market Conditions**

### Signal Types:
- **STRONG_BUY**: High confidence bullish signal
- **BUY**: Moderate confidence bullish signal  
- **HOLD**: Neutral or low confidence signal
- **SELL**: Moderate confidence bearish signal
- **STRONG_SELL**: High confidence bearish signal

## 📈 Portfolio Management

### Features:
- **Position Tracking**: Monitor all holdings and their performance
- **Risk Metrics**: Calculate volatility, beta, max drawdown
- **Performance Analytics**: Track returns, Sharpe ratio, win rate
- **Trade History**: Complete record of all transactions
- **Automated Rebalancing**: Suggestions based on analysis

### Risk Management:
- **Position Sizing**: Maximum 10% per position
- **Stop Loss**: Automatic 5% stop loss recommendations
- **Diversification**: Monitor concentration risk
- **Cash Management**: Maintain appropriate cash reserves

## 🔔 Alert System

### Slack Integration:
- Rich formatted messages with trading signals
- Portfolio updates and performance metrics
- Risk alerts and market notifications

### Email Alerts:
- HTML formatted trading recommendations
- Daily portfolio summaries
- Critical market events

### Alert Triggers:
- High-confidence buy/sell signals (>70%)
- Significant portfolio changes (>5%)
- Risk threshold breaches
- Market volatility spikes

## ⚙️ Configuration

### Key Settings (config.py):
```python
# Trading Parameters
DEFAULT_STOCKS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']
BUY_CONFIDENCE_THRESHOLD = 0.7
SELL_CONFIDENCE_THRESHOLD = 0.7
MAX_POSITION_SIZE = 0.1  # 10% max per position

# Risk Management
STOP_LOSS_THRESHOLD = 0.05  # 5% stop loss
TAKE_PROFIT_THRESHOLD = 0.15  # 15% take profit

# Analysis Settings
MARKOV_STATES = 5  # Number of price movement states
MARKOV_LOOKBACK_DAYS = 252  # 1 year of data
```

## 📝 Usage Examples

### Custom Stock Analysis:
```bash
# Analyze specific stocks
python main.py --mode analyze --symbols AAPL TSLA NVDA AMZN

# Single stock deep dive
python main.py --mode single --symbol GOOGL
```

### Portfolio Operations:
```bash
# Buy 50 shares of Apple
python main.py --mode trade --symbol AAPL --action BUY --shares 50

# Sell 25 shares of Tesla at specific price
python main.py --mode trade --symbol TSLA --action SELL --shares 25 --price 250.00
```

### Monitoring:
```bash
# Start automated monitoring (runs during market hours)
python main.py --mode schedule
```

## 🔍 Output Examples

### Analysis Output:
```
TRADE RECOMMENDATIONS
============================================================
1. BUY 45 shares of NVDA
   Price: $220.50 | Investment: $9,922.50
   Confidence: 85.2%
   Reason: Strong technical breakout with positive sentiment...

2. SELL 30 shares of TSLA  
   Price: $245.80 | Investment: $7,374.00
   Confidence: 78.9%
   Reason: Bearish divergence in RSI with negative news flow...
```

### Portfolio Summary:
```
PORTFOLIO SUMMARY
============================================================
Total Value: $125,847.32
Cash: $25,430.18
Positions: 8
Total Trades: 24

CURRENT POSITIONS:
------------------------------------------------------------
AAPL: 100 shares @ $175.25
  Value: $17,525.00 | P&L: $2,525.00 (+16.8%)
NVDA: 45 shares @ $220.50  
  Value: $9,922.50 | P&L: $1,422.50 (+16.7%)
```

## ⚠️ Risk Disclaimer

This system is for educational and research purposes. **Never invest more than you can afford to lose.** Past performance does not guarantee future results. Always do your own research and consider consulting with a financial advisor.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the logs in `trading_system.log`
2. Verify your API keys in `.env`
3. Ensure all dependencies are installed
4. Review the configuration in `config.py`

---

**Happy Trading! 🚀📈**
