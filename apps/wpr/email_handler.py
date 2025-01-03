"""Email notification handler module."""

from mailjet_rest import Client
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime

class EmailHandler:
    def __init__(self, api_key: str, api_secret: str, host: str = None, port: str = None, username: str = None, password: str = None):
        """Initialize email handler with either Mailjet or SMTP."""
        try:
            # Initialize Mailjet client
            self.mailjet = Client(auth=(api_key, api_secret), version='v3.1')
            
            # Store SMTP settings
            self.smtp_host = host
            self.smtp_port = int(port) if port else None
            self.smtp_username = username
            self.smtp_password = password
            
            self.sender_email = username or "wpr@iol.ph"
            self.sender_name = "IOL Weekly Progress Report"
            logging.info("Email handler initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize email handler: {str(e)}")
            raise
    
    def send_email(self, to_email: str, to_name: str, subject: str, html_content: str) -> Dict[str, Any]:
        """Send an email using either Mailjet or SMTP."""
        try:
            if self.smtp_host and self.smtp_port:
                return self._send_smtp_email(to_email, to_name, subject, html_content)
            else:
                return self._send_mailjet_email(to_email, to_name, subject, html_content)
        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            raise
            
    def _send_smtp_email(self, to_email: str, to_name: str, subject: str, html_content: str) -> Dict[str, Any]:
        """Send email using SMTP."""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = f"{to_name} <{to_email}>"
            
            # Attach HTML content
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                
            return {"success": True}
            
        except Exception as e:
            logging.error(f"SMTP email send failed: {str(e)}")
            raise
            
    def _send_mailjet_email(self, to_email: str, to_name: str, subject: str, html_content: str) -> Dict[str, Any]:
        """Send email using Mailjet."""
        try:
            data = {
                'Messages': [
                    {
                        "From": {
                            "Email": self.sender_email,
                            "Name": self.sender_name
                        },
                        "To": [
                            {
                                "Email": to_email,
                                "Name": to_name
                            }
                        ],
                        "Subject": subject,
                        "HTMLPart": html_content
                    }
                ]
            }
            
            result = self.mailjet.send.create(data=data)
            return result.json()
            
        except Exception as e:
            logging.error(f"Mailjet email send failed: {str(e)}")
            raise
    
    def format_hr_analysis_email(self, name: str, week_number: int, hr_analysis: Dict[str, Any]) -> str:
        """Format HR analysis for email."""
        try:
            current_date = datetime.now().strftime("%B %d, %Y")
            ai_analysis = hr_analysis.get('analysis_text', '')
            
            email_content = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                        .header {{ color: #2E86C1; margin-bottom: 20px; }}
                        .content {{ margin: 20px 0; }}
                        .footer {{ margin-top: 30px; color: #666; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>Weekly Performance Analysis</h1>
                            <h2>Week {week_number} - {current_date}</h2>
                        </div>
                        
                        <div class="content">
                            <p>Dear {name},</p>
                            {ai_analysis}
                        </div>
                        
                        {self._format_hr_analysis_section(hr_analysis)}
                        
                        <div class="footer">
                            <p>Best regards,<br>{self.sender_name}</p>
                            <p style="color: #666; font-size: 0.9em;">
                                This is an automated email from the IOL Weekly Progress Report system.
                                Please do not reply to this email.
                            </p>
                        </div>
                    </div>
                </body>
            </html>
            """
            return email_content
            
        except Exception as e:
            logging.error(f"Error formatting email content: {str(e)}")
            raise

    def format_wpr_email(self, name: str, week_number: int, 
                        ai_analysis: str, hr_analysis: Dict[str, Any] = None) -> str:
        """Format WPR email content with optional HR analysis."""
        current_date = datetime.now().strftime("%B %d, %Y")
        
        email_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                    .header {{ color: #2E86C1; margin-bottom: 20px; }}
                    .content {{ margin: 20px 0; }}
                    .footer {{ margin-top: 30px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Weekly Productivity Report Summary</h1>
                        <h2>Week {week_number}</h2>
                        <p>Date: {current_date}</p>
                    </div>
                    
                    <div class="content">
                        <p>Dear {name},</p>
                        {ai_analysis}
                    </div>
        """
        
        # Add HR analysis if available
        if hr_analysis:
            email_content += self._format_hr_analysis_section(hr_analysis)
        
        email_content += f"""
                    <div class="footer">
                        <p>Best regards,<br>{self.sender_name}</p>
                        <p style="color: #666; font-size: 0.9em;">
                            This is an automated email from the IOL Weekly Progress Report system.
                            Please do not reply to this email.
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return email_content

    def _format_hr_analysis_section(self, hr_analysis: Dict[str, Any]) -> str:
        """Format HR analysis section for email."""
        try:
            # Extract metrics with safe fallbacks
            metrics = hr_analysis.get('metrics', {})
            recommendations = hr_analysis.get('recommendations', {})
            wellness = recommendations.get('wellness_indicators', {})
            
            return f"""
                <div class="section">
                    <h2 style="color: #2E86C1;">HR Analysis Summary</h2>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                        <h3 style="color: #2471A3;">Performance Metrics</h3>
                        <ul style="list-style-type: none; padding-left: 0;">
                            <li>Productivity Score: {metrics.get('productivity_score', 'N/A')}/4</li>
                            <li>Task Completion Rate: {metrics.get('task_completion_rate', 'N/A')}%</li>
                            <li>Project Progress: {metrics.get('project_progress', 'N/A')}%</li>
                            <li>Collaboration Score: {metrics.get('collaboration_score', 'N/A')}/4</li>
                        </ul>
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                        <h3 style="color: #2471A3;">Key Recommendations</h3>
                        {self._format_list(recommendations.get('immediate_actions', []), True)}
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                        <h3 style="color: #2471A3;">Wellness Status</h3>
                        <ul style="list-style-type: none; padding-left: 0;">
                            <li>Work-Life Balance: {wellness.get('work_life_balance', 'N/A')}</li>
                            <li>Workload: {wellness.get('workload_assessment', 'N/A')}</li>
                            <li>Engagement: {wellness.get('engagement_level', 'N/A')}</li>
                        </ul>
                    </div>
                </div>
            """
        except Exception as e:
            logging.error(f"Error formatting HR analysis section: {str(e)}")
            raise

    def _format_list(self, items: List[str], as_recommendations: bool = False) -> str:
        """Format list items for email."""
        if not items:
            return "<p>None</p>"
        
        if as_recommendations:
            return "".join([
                f'<div style="padding: 10px; background-color: #E8F6F3; '
                f'border-radius: 5px; margin: 5px 0;">• {item}</div>' 
                for item in items
            ])
        
        return "<ul>" + "".join([f"<li>{item}</li>" for item in items]) + "</ul>"
    
    def _format_error_email(self, name: str, week_number: int) -> str:
        """Format error email content."""
        current_date = datetime.now().strftime("%B %d, %Y")
        return f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                    .error {{ color: #721c24; background-color: #f8d7da; padding: 15px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Weekly Performance Analysis</h1>
                    <h2>Week {week_number} - {current_date}</h2>
                    <p>Dear {name},</p>
                    <div class="error">
                        <p>We encountered an error while processing your performance analysis. 
                        Our technical team has been notified and will look into this issue.</p>
                        <p>Please try accessing your analysis again later or contact support if the issue persists.</p>
                    </div>
                    <p>Best regards,<br>{self.sender_name}</p>
                </div>
            </body>
        </html>
        """
