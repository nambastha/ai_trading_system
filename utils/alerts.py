import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging
from typing import Dict, List, Optional
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

class AlertSystem:
    def __init__(self):
        self.slack_client = None
        if Config.SLACK_BOT_TOKEN:
            self.slack_client = WebClient(token=Config.SLACK_BOT_TOKEN)
        
    def send_trading_alert(self, analysis_result: Dict, alert_type: str = "SIGNAL") -> bool:
        """Send trading alert via multiple channels"""
        success = True
        
        # Prepare alert message
        alert_message = self._format_alert_message(analysis_result, alert_type)
        
        # Send Slack notification
        if self.slack_client:
            slack_success = self._send_slack_alert(alert_message, analysis_result)
            success = success and slack_success
        
        # Send email notification
        if Config.EMAIL_USER and Config.ALERT_EMAIL:
            email_success = self._send_email_alert(alert_message, analysis_result)
            success = success and email_success
        
        return success
    
    def send_opportunity_alerts(self, opportunities: List[Dict]) -> bool:
        """Send alerts for multiple trading opportunities"""
        if not opportunities:
            return True
        
        success = True
        
        # Group by action type
        buy_opportunities = [opp for opp in opportunities if opp['action'] in ['BUY', 'STRONG_BUY']]
        sell_opportunities = [opp for opp in opportunities if opp['action'] in ['SELL', 'STRONG_SELL']]
        
        # Send buy alerts
        if buy_opportunities:
            buy_message = self._format_opportunity_message(buy_opportunities, "BUY")
            success = success and self._send_multi_channel_alert(buy_message, "🚀 BUY OPPORTUNITIES")
        
        # Send sell alerts
        if sell_opportunities:
            sell_message = self._format_opportunity_message(sell_opportunities, "SELL")
            success = success and self._send_multi_channel_alert(sell_message, "⚠️ SELL ALERTS")
        
        return success
    
    def _format_alert_message(self, analysis_result: Dict, alert_type: str) -> str:
        """Format trading alert message"""
        symbol = analysis_result.get('symbol', 'UNKNOWN')
        recommendation = analysis_result.get('final_recommendation', {})
        
        action = recommendation.get('final_recommendation', 'HOLD')
        confidence = recommendation.get('overall_confidence', 0.0)
        reasoning = recommendation.get('reasoning', 'No reasoning provided')
        current_price = analysis_result.get('current_price', 'N/A')
        risk_level = recommendation.get('risk_assessment', 'MEDIUM')
        
        # Choose emoji based on action
        emoji_map = {
            'STRONG_BUY': '🚀',
            'BUY': '📈',
            'HOLD': '⏸️',
            'SELL': '📉',
            'STRONG_SELL': '💥'
        }
        
        emoji = emoji_map.get(action, '📊')
        
        message = f"""
{emoji} **{alert_type}: {symbol}**

**Action:** {action}
**Confidence:** {confidence:.1%}
**Current Price:** ${current_price}
**Risk Level:** {risk_level}

**Analysis Summary:**
{reasoning}

**Entry Recommendations:**
• Entry Price: ${recommendation.get('entry_price', 'N/A')}
• Stop Loss: ${recommendation.get('stop_loss', 'N/A')}
• Take Profit: ${recommendation.get('take_profit', 'N/A')}
• Position Size: {recommendation.get('position_size', 'N/A')}%

**Key Risks:**
{self._format_list(recommendation.get('key_risks', []))}

**Potential Catalysts:**
{self._format_list(recommendation.get('catalysts', []))}

*Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
        """.strip()
        
        return message
    
    def _format_opportunity_message(self, opportunities: List[Dict], action_type: str) -> str:
        """Format multiple opportunities message"""
        message = f"**{action_type} OPPORTUNITIES DETECTED**\n\n"
        
        for i, opp in enumerate(opportunities[:5], 1):  # Top 5 opportunities
            symbol = opp['symbol']
            action = opp['action']
            confidence = opp['confidence']
            price = opp.get('current_price', 'N/A')
            risk = opp.get('risk_level', 'MEDIUM')
            
            message += f"{i}. **{symbol}** - {action}\n"
            message += f"   • Confidence: {confidence:.1%}\n"
            message += f"   • Price: ${price}\n"
            message += f"   • Risk: {risk}\n"
            message += f"   • Reason: {opp.get('reasoning', 'N/A')[:100]}...\n\n"
        
        if len(opportunities) > 5:
            message += f"*...and {len(opportunities) - 5} more opportunities*\n"
        
        message += f"\n*Screened at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        
        return message
    
    def _send_slack_alert(self, message: str, analysis_result: Dict) -> bool:
        """Send alert to Slack"""
        if not self.slack_client:
            logger.warning("Slack client not configured")
            return False
        
        try:
            # Create rich Slack blocks
            blocks = self._create_slack_blocks(analysis_result)
            
            response = self.slack_client.chat_postMessage(
                channel=Config.SLACK_CHANNEL,
                text=message,  # Fallback text
                blocks=blocks
            )
            
            logger.info(f"Slack alert sent successfully: {response['ts']}")
            return True
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Error sending Slack alert: {str(e)}")
            return False
    
    def _create_slack_blocks(self, analysis_result: Dict) -> List[Dict]:
        """Create Slack blocks for rich formatting"""
        symbol = analysis_result.get('symbol', 'UNKNOWN')
        recommendation = analysis_result.get('final_recommendation', {})
        
        action = recommendation.get('final_recommendation', 'HOLD')
        confidence = recommendation.get('overall_confidence', 0.0)
        current_price = analysis_result.get('current_price', 'N/A')
        
        # Color based on action
        color_map = {
            'STRONG_BUY': '#00ff00',
            'BUY': '#90ee90',
            'HOLD': '#ffff00',
            'SELL': '#ffa500',
            'STRONG_SELL': '#ff0000'
        }
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🎯 Trading Signal: {symbol}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Action:*\n{action}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Confidence:*\n{confidence:.1%}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Current Price:*\n${current_price}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Risk Level:*\n{recommendation.get('risk_assessment', 'MEDIUM')}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Reasoning:*\n{recommendation.get('reasoning', 'No reasoning provided')[:500]}..."
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
        
        return blocks
    
    def _send_email_alert(self, message: str, analysis_result: Dict) -> bool:
        """Send alert via email"""
        if not Config.EMAIL_USER or not Config.ALERT_EMAIL:
            logger.warning("Email configuration not complete")
            return False
        
        try:
            symbol = analysis_result.get('symbol', 'UNKNOWN')
            action = analysis_result.get('final_recommendation', {}).get('final_recommendation', 'HOLD')
            
            # Create email
            msg = MIMEMultipart()
            msg['From'] = Config.EMAIL_USER
            msg['To'] = Config.ALERT_EMAIL
            msg['Subject'] = f"Trading Alert: {action} {symbol}"
            
            # Convert markdown to HTML for better email formatting
            html_message = self._markdown_to_html(message)
            msg.attach(MIMEText(html_message, 'html'))
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(Config.EMAIL_HOST, Config.EMAIL_PORT) as server:
                server.starttls(context=context)
                server.login(Config.EMAIL_USER, Config.EMAIL_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email alert sent successfully to {Config.ALERT_EMAIL}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email alert: {str(e)}")
            return False
    
    def _send_multi_channel_alert(self, message: str, subject: str) -> bool:
        """Send alert to all configured channels"""
        success = True
        
        # Slack
        if self.slack_client:
            try:
                response = self.slack_client.chat_postMessage(
                    channel=Config.SLACK_CHANNEL,
                    text=message
                )
                logger.info(f"Multi-channel Slack alert sent: {response['ts']}")
            except Exception as e:
                logger.error(f"Error sending multi-channel Slack alert: {str(e)}")
                success = False
        
        # Email
        if Config.EMAIL_USER and Config.ALERT_EMAIL:
            try:
                msg = MIMEMultipart()
                msg['From'] = Config.EMAIL_USER
                msg['To'] = Config.ALERT_EMAIL
                msg['Subject'] = subject
                
                html_message = self._markdown_to_html(message)
                msg.attach(MIMEText(html_message, 'html'))
                
                context = ssl.create_default_context()
                with smtplib.SMTP(Config.EMAIL_HOST, Config.EMAIL_PORT) as server:
                    server.starttls(context=context)
                    server.login(Config.EMAIL_USER, Config.EMAIL_PASSWORD)
                    server.send_message(msg)
                
                logger.info("Multi-channel email alert sent successfully")
            except Exception as e:
                logger.error(f"Error sending multi-channel email alert: {str(e)}")
                success = False
        
        return success
    
    def _format_list(self, items: List[str]) -> str:
        """Format list items for display"""
        if not items:
            return "• None specified"
        return "\n".join([f"• {item}" for item in items[:5]])  # Top 5 items
    
    def _markdown_to_html(self, markdown_text: str) -> str:
        """Simple markdown to HTML conversion for emails"""
        html = markdown_text.replace('\n', '<br>')
        html = html.replace('**', '<strong>').replace('**', '</strong>')
        html = html.replace('*', '<em>').replace('*', '</em>')
        html = html.replace('•', '&bull;')
        
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                {html}
            </body>
        </html>
        """
