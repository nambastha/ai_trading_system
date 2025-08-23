import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
    SLACK_CHANNEL = os.getenv('SLACK_CHANNEL', '#trading-alerts')
    
    # Email Configuration
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_USER = os.getenv('EMAIL_USER')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    ALERT_EMAIL = os.getenv('ALERT_EMAIL')
    
    # Trading Configuration
    DEFAULT_STOCKS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'AMZN', 'META']
    MARKOV_LOOKBACK_DAYS = 252  # 1 year of trading days
    MARKOV_STATES = 5  # Number of price movement states
    
    # Risk Management
    MAX_POSITION_SIZE = 0.1  # 10% of portfolio per position
    STOP_LOSS_THRESHOLD = 0.05  # 5% stop loss
    TAKE_PROFIT_THRESHOLD = 0.15  # 15% take profit
    
    # Alert Thresholds
    BUY_CONFIDENCE_THRESHOLD = 0.7
    SELL_CONFIDENCE_THRESHOLD = 0.7
    
    # Data Configuration
    DATA_REFRESH_INTERVAL = 300  # 5 minutes in seconds
    HISTORICAL_DATA_PERIOD = '2y'  # 2 years of historical data
