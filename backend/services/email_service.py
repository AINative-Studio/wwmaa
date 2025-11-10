"""
Email Service for WWMAA Backend

Provides email sending functionality using Postmark for transactional emails.
Includes verification emails, password reset, and other notifications.
"""

import logging
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from backend.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class EmailServiceError(Exception):
    """Base exception for email service errors"""
    pass


class EmailSendError(EmailServiceError):
    """Exception raised when email sending fails"""
    pass


class EmailService:
    """
    Email service using Postmark API

    Provides methods for sending transactional emails including:
    - Email verification
    - Password reset
    - Welcome emails
    - Notification emails
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        from_email: Optional[str] = None
    ):
        """
        Initialize Email Service

        Args:
            api_key: Postmark API key (defaults to settings.POSTMARK_API_KEY)
            from_email: Sender email address (defaults to settings.FROM_EMAIL)
        """
        self.api_key = api_key or settings.POSTMARK_API_KEY
        self.from_email = from_email or settings.FROM_EMAIL
        self.base_url = "https://api.postmarkapp.com"

        if not self.api_key:
            raise EmailServiceError("POSTMARK_API_KEY is required")

        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Postmark-Server-Token": self.api_key
        }

        logger.info(f"EmailService initialized with sender: {self.from_email}")

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        tag: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send an email via Postmark API

        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_body: HTML email body
            text_body: Plain text email body (optional)
            tag: Email tag for categorization (optional)
            metadata: Additional metadata (optional)

        Returns:
            Postmark API response

        Raises:
            EmailSendError: If email sending fails
        """
        url = f"{self.base_url}/email"

        payload = {
            "From": self.from_email,
            "To": to_email,
            "Subject": subject,
            "HtmlBody": html_body,
            "MessageStream": "outbound"
        }

        if text_body:
            payload["TextBody"] = text_body

        if tag:
            payload["Tag"] = tag

        if metadata:
            payload["Metadata"] = metadata

        logger.info(f"Sending email to {to_email} with subject: {subject}")

        try:
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                message_id = result.get("MessageID")
                logger.info(f"Email sent successfully. MessageID: {message_id}")
                return result
            else:
                # Try to parse JSON error response
                try:
                    error_data = response.json()
                    error_message = error_data.get("Message", response.text)
                except ValueError:
                    error_message = response.text or "Unknown error"

                logger.error(f"Failed to send email: {error_message}")
                raise EmailSendError(f"Failed to send email: {error_message}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Email sending request failed: {e}")
            raise EmailSendError(f"Email sending request failed: {e}")

    def send_verification_email(
        self,
        email: str,
        token: str,
        user_name: str
    ) -> Dict[str, Any]:
        """
        Send email verification email to new user

        Args:
            email: User's email address
            token: Verification token
            user_name: User's name for personalization

        Returns:
            Postmark API response

        Raises:
            EmailSendError: If email sending fails
        """
        # Construct verification URL
        frontend_url = settings.PYTHON_BACKEND_URL.replace(":8000", ":3000")
        verification_url = f"{frontend_url}/verify-email?token={token}"

        subject = "Verify Your WWMAA Account"

        # HTML email body
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #8B0000;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .button {{
                    display: inline-block;
                    background-color: #8B0000;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Women's Martial Arts Association of America</h1>
            </div>
            <div class="content">
                <h2>Welcome, {user_name}!</h2>
                <p>Thank you for registering with the Women's Martial Arts Association of America. We're excited to have you join our community of martial artists.</p>

                <p>To complete your registration and activate your account, please verify your email address by clicking the button below:</p>

                <div style="text-align: center;">
                    <a href="{verification_url}" class="button">Verify Email Address</a>
                </div>

                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; background: white; padding: 10px; border-radius: 3px;">
                    {verification_url}
                </p>

                <div class="warning">
                    <strong>Important:</strong> This verification link will expire in 24 hours. If you don't verify your email within this time, you'll need to request a new verification email.
                </div>

                <p>If you didn't create this account, please ignore this email and the account will not be activated.</p>
            </div>
            <div class="footer">
                <p>Women's Martial Arts Association of America</p>
                <p>This is an automated message, please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """

        # Plain text version for email clients that don't support HTML
        text_body = f"""
        Welcome to WWMAA, {user_name}!

        Thank you for registering with the Women's Martial Arts Association of America.

        To complete your registration and activate your account, please verify your email address by visiting:

        {verification_url}

        IMPORTANT: This verification link will expire in 24 hours.

        If you didn't create this account, please ignore this email.

        ---
        Women's Martial Arts Association of America
        This is an automated message, please do not reply to this email.
        """

        return self._send_email(
            to_email=email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            tag="email-verification",
            metadata={
                "user_email": email,
                "user_name": user_name
            }
        )

    def send_welcome_email(
        self,
        email: str,
        user_name: str
    ) -> Dict[str, Any]:
        """
        Send welcome email after successful verification

        Args:
            email: User's email address
            user_name: User's name for personalization

        Returns:
            Postmark API response

        Raises:
            EmailSendError: If email sending fails
        """
        subject = "Welcome to WWMAA - Your Account is Active!"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #8B0000;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Welcome to WWMAA!</h1>
            </div>
            <div class="content">
                <h2>Hello, {user_name}!</h2>
                <p>Your email has been successfully verified and your WWMAA account is now active!</p>

                <p>You can now access all member features and benefits. Here's what you can do next:</p>

                <ul>
                    <li>Complete your member profile</li>
                    <li>Browse upcoming events and training sessions</li>
                    <li>Connect with other members</li>
                    <li>Access exclusive content and resources</li>
                </ul>

                <p>If you have any questions or need assistance, please don't hesitate to contact us.</p>

                <p>We look forward to supporting your martial arts journey!</p>
            </div>
            <div class="footer">
                <p>Women's Martial Arts Association of America</p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Welcome to WWMAA, {user_name}!

        Your email has been successfully verified and your WWMAA account is now active!

        You can now access all member features and benefits.

        ---
        Women's Martial Arts Association of America
        """

        return self._send_email(
            to_email=email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            tag="welcome",
            metadata={
                "user_email": email,
                "user_name": user_name
            }
        )

    def send_password_reset_email(
        self,
        email: str,
        token: str,
        user_name: str
    ) -> Dict[str, Any]:
        """
        Send password reset email

        Args:
            email: User's email address
            token: Password reset token
            user_name: User's name for personalization

        Returns:
            Postmark API response

        Raises:
            EmailSendError: If email sending fails
        """
        # Construct reset URL
        frontend_url = settings.PYTHON_BACKEND_URL.replace(":8000", ":3000")
        reset_url = f"{frontend_url}/reset-password?token={token}"

        subject = "Reset Your WWMAA Password"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #8B0000;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .button {{
                    display: inline-block;
                    background-color: #8B0000;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Password Reset Request</h1>
            </div>
            <div class="content">
                <h2>Hello, {user_name}</h2>
                <p>We received a request to reset your WWMAA account password.</p>

                <p>Click the button below to reset your password:</p>

                <div style="text-align: center;">
                    <a href="{reset_url}" class="button">Reset Password</a>
                </div>

                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; background: white; padding: 10px; border-radius: 3px;">
                    {reset_url}
                </p>

                <div class="warning">
                    <strong>Important:</strong> This password reset link will expire in 1 hour. If you don't reset your password within this time, you'll need to request a new reset link.
                </div>

                <p>If you didn't request a password reset, please ignore this email and your password will remain unchanged.</p>
            </div>
            <div class="footer">
                <p>Women's Martial Arts Association of America</p>
                <p>This is an automated message, please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Password Reset Request

        Hello, {user_name}

        We received a request to reset your WWMAA account password.

        To reset your password, visit:

        {reset_url}

        IMPORTANT: This password reset link will expire in 1 hour.

        If you didn't request a password reset, please ignore this email.

        ---
        Women's Martial Arts Association of America
        This is an automated message, please do not reply to this email.
        """

        return self._send_email(
            to_email=email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            tag="password-reset",
            metadata={
                "user_email": email,
                "user_name": user_name
            }
        )

    def send_password_changed_email(
        self,
        email: str,
        user_name: str
    ) -> Dict[str, Any]:
        """
        Send password change confirmation email

        Args:
            email: User's email address
            user_name: User's name for personalization

        Returns:
            Postmark API response

        Raises:
            EmailSendError: If email sending fails
        """
        subject = "WWMAA Password Changed Successfully"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #8B0000;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
                .alert {{
                    background-color: #d4edda;
                    border-left: 4px solid #28a745;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Password Changed Successfully</h1>
            </div>
            <div class="content">
                <h2>Hello, {user_name}</h2>

                <div class="alert">
                    <strong>Success!</strong> Your WWMAA account password has been changed successfully.
                </div>

                <p>This email confirms that your password was recently changed. You can now use your new password to log in to your account.</p>

                <p><strong>Security Information:</strong></p>
                <ul>
                    <li>Date: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}</li>
                    <li>All existing sessions have been invalidated for security</li>
                    <li>You will need to log in again with your new password</li>
                </ul>

                <div class="warning">
                    <strong>Didn't change your password?</strong> If you did not make this change, please contact us immediately and secure your account.
                </div>

                <p>For security reasons, we recommend that you:</p>
                <ul>
                    <li>Use a strong, unique password for your account</li>
                    <li>Enable two-factor authentication if available</li>
                    <li>Never share your password with anyone</li>
                </ul>
            </div>
            <div class="footer">
                <p>Women's Martial Arts Association of America</p>
                <p>This is an automated message, please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Password Changed Successfully

        Hello, {user_name}

        This email confirms that your WWMAA account password has been changed successfully.

        Date: {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p UTC')}

        All existing sessions have been invalidated for security. You will need to log in again with your new password.

        IMPORTANT: If you did not make this change, please contact us immediately.

        ---
        Women's Martial Arts Association of America
        This is an automated message, please do not reply to this email.
        """

        return self._send_email(
            to_email=email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            tag="password-changed",
            metadata={
                "user_email": email,
                "user_name": user_name
            }
        )


# Global email service instance (singleton pattern)
_email_service_instance: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """
    Get or create the global EmailService instance

    Returns:
        EmailService instance
    """
    global _email_service_instance

    if _email_service_instance is None:
        _email_service_instance = EmailService()

    return _email_service_instance
