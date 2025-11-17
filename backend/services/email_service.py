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

    def send_application_rejection_email(
        self,
        email: str,
        user_name: str,
        rejection_reason: Optional[str] = None,
        recommended_improvements: Optional[str] = None,
        allow_reapplication: bool = True,
        reapplication_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Send application rejection email to applicant

        Args:
            email: Applicant's email address
            user_name: Applicant's name for personalization
            rejection_reason: Reason for rejection (optional)
            recommended_improvements: Recommended improvements (optional)
            allow_reapplication: Whether applicant can reapply
            reapplication_date: Date when reapplication is allowed (optional)

        Returns:
            Postmark API response

        Raises:
            EmailSendError: If email sending fails
        """
        subject = "WWMAA Membership Application Decision"

        # Format reapplication date if provided
        reapplication_info = ""
        if allow_reapplication and reapplication_date:
            formatted_date = reapplication_date.strftime('%B %d, %Y')
            reapplication_info = f"<p>You are welcome to reapply for membership starting on <strong>{formatted_date}</strong> (30 days from now).</p>"
        elif allow_reapplication:
            reapplication_info = "<p>You are welcome to reapply for membership at any time.</p>"
        else:
            reapplication_info = "<p>Unfortunately, you are not eligible to reapply for membership at this time.</p>"

        # Build rejection reason section
        reason_section = ""
        if rejection_reason:
            reason_section = f"""
            <div class="info-box">
                <h3>Reason for Decision</h3>
                <p>{rejection_reason}</p>
            </div>
            """

        # Build recommended improvements section
        improvements_section = ""
        if recommended_improvements:
            improvements_section = f"""
            <div class="info-box" style="background-color: #e7f3ff; border-left: 4px solid #2196F3;">
                <h3>Recommendations for Future Applications</h3>
                <p>{recommended_improvements}</p>
            </div>
            """

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
                .info-box {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .info-box h3 {{
                    margin-top: 0;
                    color: #333;
                }}
                .contact-box {{
                    background-color: #e7f3ff;
                    border-left: 4px solid #2196F3;
                    padding: 15px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Membership Application Decision</h1>
            </div>
            <div class="content">
                <h2>Dear {user_name},</h2>

                <p>Thank you for your interest in joining the Women's Martial Arts Association of America. We appreciate the time and effort you put into your membership application.</p>

                <p>After careful review by our board members, we regret to inform you that we are unable to approve your membership application at this time.</p>

                {reason_section}

                {improvements_section}

                {reapplication_info}

                <div class="contact-box">
                    <h3>Questions or Concerns?</h3>
                    <p>If you have any questions about this decision or would like additional feedback, please don't hesitate to contact us:</p>
                    <ul>
                        <li><strong>Email:</strong> membership@wwmaa.org</li>
                        <li><strong>Phone:</strong> (555) 123-4567</li>
                    </ul>
                    <p>We're here to help and provide guidance for your martial arts journey.</p>
                </div>

                <p>We wish you the best in your martial arts training and future endeavors.</p>

                <p>Sincerely,<br>
                <strong>WWMAA Membership Committee</strong></p>
            </div>
            <div class="footer">
                <p>Women's Martial Arts Association of America</p>
                <p>This is an automated message, but we welcome your replies to membership@wwmaa.org</p>
            </div>
        </body>
        </html>
        """

        # Plain text version
        text_reason = f"\n\nReason for Decision:\n{rejection_reason}\n" if rejection_reason else ""
        text_improvements = f"\nRecommendations for Future Applications:\n{recommended_improvements}\n" if recommended_improvements else ""

        text_reapplication = ""
        if allow_reapplication and reapplication_date:
            formatted_date = reapplication_date.strftime('%B %d, %Y')
            text_reapplication = f"\nYou are welcome to reapply for membership starting on {formatted_date} (30 days from now).\n"
        elif allow_reapplication:
            text_reapplication = "\nYou are welcome to reapply for membership at any time.\n"
        else:
            text_reapplication = "\nUnfortunately, you are not eligible to reapply for membership at this time.\n"

        text_body = f"""
        Membership Application Decision

        Dear {user_name},

        Thank you for your interest in joining the Women's Martial Arts Association of America. We appreciate the time and effort you put into your membership application.

        After careful review by our board members, we regret to inform you that we are unable to approve your membership application at this time.
        {text_reason}{text_improvements}{text_reapplication}
        Questions or Concerns?
        If you have any questions about this decision or would like additional feedback, please don't hesitate to contact us:

        Email: membership@wwmaa.org
        Phone: (555) 123-4567

        We're here to help and provide guidance for your martial arts journey.

        We wish you the best in your martial arts training and future endeavors.

        Sincerely,
        WWMAA Membership Committee

        ---
        Women's Martial Arts Association of America
        This is an automated message, but we welcome your replies to membership@wwmaa.org
        """

        return self._send_email(
            to_email=email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            tag="application-rejection",
            metadata={
                "user_email": email,
                "user_name": user_name,
                "allow_reapplication": str(allow_reapplication)
            }
        )

    def send_application_first_approval_email(
        self,
        email: str,
        applicant_name: str,
        approver_name: str,
        approvals_count: int
    ) -> Dict[str, Any]:
        """
        Send email when application receives first board approval

        Args:
            email: Applicant's email address
            applicant_name: Applicant's name for personalization
            approver_name: Name/email of the board member who approved
            approvals_count: Current number of approvals

        Returns:
            Postmark API response

        Raises:
            EmailSendError: If email sending fails
        """
        subject = "WWMAA Application - Board Approval Received"

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
                .info {{
                    background-color: #d1ecf1;
                    border-left: 4px solid #17a2b8;
                    padding: 15px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Application Update</h1>
            </div>
            <div class="content">
                <h2>Hello, {applicant_name}!</h2>

                <div class="alert">
                    <strong>Good News!</strong> Your WWMAA membership application has received board approval.
                </div>

                <p>We're pleased to inform you that a board member has reviewed and approved your membership application.</p>

                <div class="info">
                    <strong>Application Status:</strong><br>
                    Approvals Received: {approvals_count} of 2<br>
                    Status: Under Review
                </div>

                <p>Your application requires approval from two board members. You've received your first approval, and we're waiting for the second review.</p>

                <p>Once your application receives the second approval, you'll be notified immediately and your membership will be activated.</p>

                <p>Thank you for your patience during this process!</p>
            </div>
            <div class="footer">
                <p>Women's Martial Arts Association of America</p>
                <p>This is an automated message, please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Application Update

        Hello, {applicant_name}!

        Good News! Your WWMAA membership application has received board approval.

        Application Status:
        - Approvals Received: {approvals_count} of 2
        - Status: Under Review

        Your application requires approval from two board members. You've received your first approval, and we're waiting for the second review.

        Once your application receives the second approval, you'll be notified immediately and your membership will be activated.

        Thank you for your patience during this process!

        ---
        Women's Martial Arts Association of America
        This is an automated message, please do not reply to this email.
        """

        return self._send_email(
            to_email=email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            tag="application-first-approval",
            metadata={
                "applicant_email": email,
                "applicant_name": applicant_name,
                "approvals_count": str(approvals_count)
            }
        )

    def send_application_fully_approved_email(
        self,
        email: str,
        applicant_name: str
    ) -> Dict[str, Any]:
        """
        Send email when application is fully approved (2 approvals received)

        Args:
            email: Applicant's email address
            applicant_name: Applicant's name for personalization

        Returns:
            Postmark API response

        Raises:
            EmailSendError: If email sending fails
        """
        frontend_url = settings.PYTHON_BACKEND_URL.replace(":8000", ":3000")
        dashboard_url = f"{frontend_url}/dashboard"

        subject = "Congratulations! Your WWMAA Membership is Approved"

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
                .success {{
                    background-color: #d4edda;
                    border-left: 4px solid #28a745;
                    padding: 15px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Membership Approved!</h1>
            </div>
            <div class="content">
                <h2>Congratulations, {applicant_name}!</h2>

                <div class="success">
                    <strong>Welcome to WWMAA!</strong> Your membership application has been fully approved by our board.
                </div>

                <p>We are thrilled to welcome you to the Women's Martial Arts Association of America. Your application has received the required approvals from our board members, and your membership is now active.</p>

                <p><strong>What's Next?</strong></p>
                <ul>
                    <li>Access your member dashboard to complete your profile</li>
                    <li>Browse and register for upcoming events and training sessions</li>
                    <li>Connect with other members in our community</li>
                    <li>Access exclusive resources and training materials</li>
                </ul>

                <div style="text-align: center;">
                    <a href="{dashboard_url}" class="button">Access Your Dashboard</a>
                </div>

                <p>If you have any questions or need assistance getting started, please don't hesitate to reach out.</p>

                <p>We look forward to supporting your martial arts journey!</p>
            </div>
            <div class="footer">
                <p>Women's Martial Arts Association of America</p>
                <p>This is an automated message, please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Membership Approved!

        Congratulations, {applicant_name}!

        Welcome to WWMAA! Your membership application has been fully approved by our board.

        We are thrilled to welcome you to the Women's Martial Arts Association of America. Your application has received the required approvals from our board members, and your membership is now active.

        What's Next?
        - Access your member dashboard to complete your profile
        - Browse and register for upcoming events and training sessions
        - Connect with other members in our community
        - Access exclusive resources and training materials

        Access your dashboard: {dashboard_url}

        If you have any questions or need assistance getting started, please don't hesitate to reach out.

        We look forward to supporting your martial arts journey!

        ---
        Women's Martial Arts Association of America
        This is an automated message, please do not reply to this email.
        """

        return self._send_email(
            to_email=email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            tag="application-fully-approved",
            metadata={
                "applicant_email": email,
                "applicant_name": applicant_name
            }
        )

    def send_application_rejected_email(
        self,
        email: str,
        applicant_name: str,
        rejection_reason: str
    ) -> Dict[str, Any]:
        """
        Send email when application is rejected (simplified version for workflow)

        Args:
            email: Applicant's email address
            applicant_name: Applicant's name for personalization
            rejection_reason: Reason for rejection

        Returns:
            Postmark API response

        Raises:
            EmailSendError: If email sending fails
        """
        # Use the existing send_application_rejection_email method with defaults
        return self.send_application_rejection_email(
            email=email,
            user_name=applicant_name,
            rejection_reason=rejection_reason,
            recommended_improvements=None,
            allow_reapplication=True,
            reapplication_date=None
        )

    def send_board_member_new_application_notification(
        self,
        email: str,
        board_member_name: str,
        applicant_name: str,
        applicant_email: str,
        martial_arts_style: str,
        years_experience: int
    ) -> Dict[str, Any]:
        """
        Send notification to board member when new application submitted

        Args:
            email: Board member's email address
            board_member_name: Board member's name
            applicant_name: Applicant's full name
            applicant_email: Applicant's email
            martial_arts_style: Applicant's martial arts style
            years_experience: Years of experience

        Returns:
            Postmark API response

        Raises:
            EmailSendError: If email sending fails
        """
        frontend_url = settings.PYTHON_BACKEND_URL.replace(":8000", ":3000")
        dashboard_url = f"{frontend_url}/dashboard/board"

        subject = "New Membership Application - Action Required"

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
                .info {{
                    background-color: #d1ecf1;
                    border-left: 4px solid #17a2b8;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .alert {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>New Application Submitted</h1>
            </div>
            <div class="content">
                <h2>Hello, {board_member_name}</h2>

                <div class="alert">
                    <strong>Action Required:</strong> A new membership application needs your review.
                </div>

                <p>A new member has applied to join the Women's Martial Arts Association of America and requires board approval.</p>

                <div class="info">
                    <h3 style="margin-top: 0;">Applicant Information:</h3>
                    <ul style="margin-bottom: 0;">
                        <li><strong>Name:</strong> {applicant_name}</li>
                        <li><strong>Email:</strong> {applicant_email}</li>
                        <li><strong>Martial Arts Style:</strong> {martial_arts_style}</li>
                        <li><strong>Years of Experience:</strong> {years_experience}</li>
                    </ul>
                </div>

                <p><strong>Required Action:</strong></p>
                <p>This application requires approval from 2 board members. Please review the full application and cast your vote (approve or reject) in the Board Member Dashboard.</p>

                <div style="text-align: center;">
                    <a href="{dashboard_url}" class="button">Review Application</a>
                </div>

                <p><strong>Timeline:</strong> Applications should be reviewed within 5 business days to ensure a prompt response to applicants.</p>

                <p>If you have any questions about this application or the review process, please contact the Membership Committee.</p>
            </div>
            <div class="footer">
                <p>Women's Martial Arts Association of America</p>
                <p>Board Member Portal</p>
                <p>This is an automated message, please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        New Application Submitted

        Hello, {board_member_name}

        ACTION REQUIRED: A new membership application needs your review.

        Applicant Information:
        - Name: {applicant_name}
        - Email: {applicant_email}
        - Martial Arts Style: {martial_arts_style}
        - Years of Experience: {years_experience}

        Required Action:
        This application requires approval from 2 board members. Please review the full application and cast your vote in the Board Member Dashboard.

        Review Application: {dashboard_url}

        Timeline: Applications should be reviewed within 5 business days.

        ---
        Women's Martial Arts Association of America
        Board Member Portal
        This is an automated message, please do not reply to this email.
        """

        return self._send_email(
            to_email=email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            tag="board-new-application",
            metadata={
                "board_member_email": email,
                "board_member_name": board_member_name,
                "applicant_name": applicant_name,
                "applicant_email": applicant_email
            }
        )

    def send_application_info_request_email(
        self,
        email: str,
        applicant_name: str,
        request_message: str,
        reviewer_name: str
    ) -> Dict[str, Any]:
        """
        Send email when board member requests additional information

        Args:
            email: Applicant's email address
            applicant_name: Applicant's name for personalization
            request_message: Message from board member
            reviewer_name: Name of the board member requesting info

        Returns:
            Postmark API response

        Raises:
            EmailSendError: If email sending fails
        """
        frontend_url = settings.PYTHON_BACKEND_URL.replace(":8000", ":3000")
        application_url = f"{frontend_url}/dashboard/application"

        subject = "WWMAA Application - Additional Information Requested"

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
                .info {{
                    background-color: #d1ecf1;
                    border-left: 4px solid #17a2b8;
                    padding: 15px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Application Update</h1>
            </div>
            <div class="content">
                <h2>Hello, {applicant_name}!</h2>

                <p>Your WWMAA membership application is being reviewed by our board. A board member has requested some additional information to help complete the review process.</p>

                <div class="info">
                    <strong>Request from {reviewer_name}:</strong><br>
                    {request_message}
                </div>

                <p>Please log in to your account to update your application with the requested information.</p>

                <div style="text-align: center;">
                    <a href="{application_url}" class="button">Update Application</a>
                </div>

                <p>Providing this additional information will help us process your application more efficiently.</p>

                <p>Thank you for your cooperation!</p>
            </div>
            <div class="footer">
                <p>Women's Martial Arts Association of America</p>
                <p>This is an automated message, please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Application Update

        Hello, {applicant_name}!

        Your WWMAA membership application is being reviewed by our board. A board member has requested some additional information to help complete the review process.

        Request from {reviewer_name}:
        {request_message}

        Please log in to your account to update your application with the requested information.

        Update your application: {application_url}

        Providing this additional information will help us process your application more efficiently.

        Thank you for your cooperation!

        ---
        Women's Martial Arts Association of America
        This is an automated message, please do not reply to this email.
        """

        return self._send_email(
            to_email=email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            tag="application-info-request",
            metadata={
                "applicant_email": email,
                "applicant_name": applicant_name,
                "reviewer_name": reviewer_name
            }
        )

    def send_payment_link_email(
        self,
        email: str,
        applicant_name: str,
        payment_url: str,
        tier_name: str,
        amount: str
    ) -> Dict[str, Any]:
        """
        Send payment link email after application approval

        Args:
            email: Applicant's email address
            applicant_name: Applicant's name for personalization
            payment_url: Stripe checkout URL
            tier_name: Membership tier name
            amount: Payment amount (formatted string)

        Returns:
            Postmark API response

        Raises:
            EmailSendError: If email sending fails
        """
        subject = "Complete Your WWMAA Membership Payment"

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
                    background-color: #28a745;
                    color: white;
                    padding: 15px 40px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                    font-size: 18px;
                    font-weight: bold;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
                .success {{
                    background-color: #d4edda;
                    border-left: 4px solid #28a745;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .info-box {{
                    background-color: #e7f3ff;
                    border-left: 4px solid #2196F3;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .price {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #8B0000;
                    text-align: center;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Payment Required</h1>
            </div>
            <div class="content">
                <h2>Congratulations, {applicant_name}!</h2>

                <div class="success">
                    <strong>Great News!</strong> Your WWMAA membership application has been approved by our board!
                </div>

                <p>We're excited to welcome you to the Women's Martial Arts Association of America. To complete your membership activation, please proceed with your payment.</p>

                <div class="info-box">
                    <strong>Membership Details:</strong><br>
                    Tier: {tier_name}<br>
                    <div class="price">{amount}</div>
                </div>

                <p><strong>Next Steps:</strong></p>
                <ol>
                    <li>Click the payment button below to proceed to our secure checkout</li>
                    <li>Enter your payment information (processed securely by Stripe)</li>
                    <li>Complete your payment</li>
                    <li>Start enjoying your WWMAA membership benefits!</li>
                </ol>

                <div style="text-align: center;">
                    <a href="{payment_url}" class="button">Complete Payment</a>
                </div>

                <p style="word-break: break-all; background: white; padding: 10px; border-radius: 3px; font-size: 12px;">
                    Or copy and paste this link: {payment_url}
                </p>

                <div class="info-box">
                    <strong>Payment Security:</strong><br>
                    Your payment is processed securely through Stripe, an industry-leading payment processor. We never store your credit card information. This payment link will expire in 30 minutes for your security.
                </div>

                <p><strong>What's Included with Your Membership:</strong></p>
                <ul>
                    <li>Access to all member-only events and training sessions</li>
                    <li>Member directory and networking opportunities</li>
                    <li>Exclusive training videos and resources</li>
                    <li>Monthly newsletter with martial arts tips and community updates</li>
                    <li>Discounts on events and merchandise</li>
                </ul>

                <p>If you have any questions or need assistance, please don't hesitate to contact us at membership@wwmaa.org.</p>

                <p>We look forward to supporting your martial arts journey!</p>

                <p>Sincerely,<br>
                <strong>WWMAA Membership Team</strong></p>
            </div>
            <div class="footer">
                <p>Women's Martial Arts Association of America</p>
                <p>This is an automated message. If you need help, contact membership@wwmaa.org</p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Payment Required

        Congratulations, {applicant_name}!

        Great News! Your WWMAA membership application has been approved by our board!

        We're excited to welcome you to the Women's Martial Arts Association of America. To complete your membership activation, please proceed with your payment.

        Membership Details:
        - Tier: {tier_name}
        - Amount: {amount}

        Next Steps:
        1. Visit the payment link below to proceed to our secure checkout
        2. Enter your payment information (processed securely by Stripe)
        3. Complete your payment
        4. Start enjoying your WWMAA membership benefits!

        Payment Link:
        {payment_url}

        Payment Security:
        Your payment is processed securely through Stripe. We never store your credit card information. This payment link will expire in 30 minutes for your security.

        What's Included with Your Membership:
        - Access to all member-only events and training sessions
        - Member directory and networking opportunities
        - Exclusive training videos and resources
        - Monthly newsletter with martial arts tips
        - Discounts on events and merchandise

        If you have any questions, contact us at membership@wwmaa.org.

        We look forward to supporting your martial arts journey!

        Sincerely,
        WWMAA Membership Team

        ---
        Women's Martial Arts Association of America
        """

        return self._send_email(
            to_email=email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            tag="payment-link",
            metadata={
                "applicant_email": email,
                "applicant_name": applicant_name,
                "tier_name": tier_name,
                "amount": amount
            }
        )

    def send_payment_success_email(
        self,
        email: str,
        user_name: str,
        amount: float,
        currency: str = "USD",
        receipt_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send payment success confirmation email

        Args:
            email: User's email address
            user_name: User's name for personalization
            amount: Payment amount
            currency: Currency code (default: USD)
            receipt_url: URL to payment receipt (optional)

        Returns:
            Postmark API response

        Raises:
            EmailSendError: If email sending fails
        """
        subject = "Payment Successful - WWMAA Membership"

        # Format amount with currency symbol
        currency_symbols = {"USD": "$", "EUR": "€", "GBP": "£"}
        symbol = currency_symbols.get(currency.upper(), currency)
        formatted_amount = f"{symbol}{amount:.2f}"

        # Build receipt section
        receipt_section = ""
        if receipt_url:
            receipt_section = f'<div style="text-align: center;"><a href="{receipt_url}" class="button">View Receipt</a></div>'

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;}}
                .header {{background-color: #8B0000; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0;}}
                .content {{background-color: #f9f9f9; padding: 30px; border-radius: 0 0 5px 5px;}}
                .button {{display: inline-block; background-color: #8B0000; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0;}}
                .footer {{margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; text-align: center;}}
                .success {{background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0;}}
            </style>
        </head>
        <body>
            <div class="header"><h1>Payment Successful</h1></div>
            <div class="content">
                <h2>Thank you, {user_name}!</h2>
                <div class="success"><strong>Your payment has been processed successfully.</strong></div>
                <p>Amount Paid: {formatted_amount} {currency}<br>Date: {datetime.utcnow().strftime('%B %d, %Y')}</p>
                {receipt_section}
                <p>Your WWMAA membership is now active with full member benefits!</p>
            </div>
            <div class="footer"><p>Women's Martial Arts Association of America</p></div>
        </body>
        </html>
        """

        text_body = f"Payment Successful\n\nThank you, {user_name}!\n\nAmount: {formatted_amount} {currency}\nDate: {datetime.utcnow().strftime('%B %d, %Y')}\n\nYour membership is now active!"

        return self._send_email(to_email=email, subject=subject, html_body=html_body, text_body=text_body, tag="payment-success")

    def send_payment_failed_email(self, email: str, user_name: str, amount: float, currency: str = "USD") -> Dict[str, Any]:
        """Send payment failed (dunning) email"""
        subject = "Payment Failed - WWMAA Membership"
        currency_symbols = {"USD": "$", "EUR": "€", "GBP": "£"}
        symbol = currency_symbols.get(currency.upper(), currency)
        formatted_amount = f"{symbol}{amount:.2f}"
        frontend_url = settings.PYTHON_BACKEND_URL.replace(":8000", ":3000")
        payment_url = f"{frontend_url}/dashboard/billing"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            body {{font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;}}
            .header {{background-color: #8B0000; color: white; padding: 20px; text-align: center;}}
            .content {{background-color: #f9f9f9; padding: 30px;}}
            .warning {{background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;}}
            .button {{display: inline-block; background-color: #8B0000; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;}}
        </style></head>
        <body>
            <div class="header"><h1>Payment Failed</h1></div>
            <div class="content">
                <h2>Hello, {user_name}</h2>
                <div class="warning"><strong>Action Required:</strong> We were unable to process your payment of {formatted_amount} {currency}.</div>
                <p>Please update your payment method to avoid service interruption.</p>
                <div style="text-align: center;"><a href="{payment_url}" class="button">Update Payment Method</a></div>
            </div>
        </body>
        </html>
        """

        text_body = f"Payment Failed\n\nHello, {user_name}\n\nWe were unable to process your payment of {formatted_amount} {currency}.\n\nPlease update your payment method: {payment_url}"

        return self._send_email(to_email=email, subject=subject, html_body=html_body, text_body=text_body, tag="payment-failed")

    def send_subscription_canceled_email(self, email: str, user_name: str) -> Dict[str, Any]:
        """Send subscription cancellation confirmation email"""
        subject = "Subscription Canceled - WWMAA"
        frontend_url = settings.PYTHON_BACKEND_URL.replace(":8000", ":3000")

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            body {{font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;}}
            .header {{background-color: #8B0000; color: white; padding: 20px; text-align: center;}}
            .content {{background-color: #f9f9f9; padding: 30px;}}
        </style></head>
        <body>
            <div class="header"><h1>Subscription Canceled</h1></div>
            <div class="content">
                <h2>Hello, {user_name}</h2>
                <p>Your WWMAA membership has been canceled. We're sorry to see you go!</p>
                <p>You can reactivate anytime at: {frontend_url}/membership</p>
            </div>
        </body>
        </html>
        """

        text_body = f"Subscription Canceled\n\nHello, {user_name}\n\nYour membership has been canceled. Reactivate anytime at: {frontend_url}/membership"

        return self._send_email(to_email=email, subject=subject, html_body=html_body, text_body=text_body, tag="subscription-canceled")

    def send_refund_confirmation_email(self, email: str, user_name: str, amount: float, currency: str = "USD") -> Dict[str, Any]:
        """Send refund confirmation email"""
        subject = "Refund Processed - WWMAA"
        currency_symbols = {"USD": "$", "EUR": "€", "GBP": "£"}
        symbol = currency_symbols.get(currency.upper(), currency)
        formatted_amount = f"{symbol}{amount:.2f}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            body {{font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;}}
            .header {{background-color: #8B0000; color: white; padding: 20px; text-align: center;}}
            .content {{background-color: #f9f9f9; padding: 30px;}}
            .success {{background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px;}}
        </style></head>
        <body>
            <div class="header"><h1>Refund Processed</h1></div>
            <div class="content">
                <h2>Hello, {user_name}</h2>
                <div class="success"><strong>Your refund of {formatted_amount} {currency} has been processed.</strong></div>
                <p>The refund should appear in your account within 5-10 business days.</p>
            </div>
        </body>
        </html>
        """

        text_body = f"Refund Processed\n\nHello, {user_name}\n\nYour refund of {formatted_amount} {currency} has been processed and should appear in 5-10 business days."

        return self._send_email(to_email=email, subject=subject, html_body=html_body, text_body=text_body, tag="refund-confirmation")

    def send_free_event_rsvp_confirmation(
        self,
        email: str,
        user_name: str,
        event_title: str,
        event_date: str,
        event_location: Optional[str] = None,
        event_address: Optional[str] = None,
        qr_code: Optional[str] = None,
        rsvp_id: Optional[str] = None,
        from_waitlist: bool = False
    ) -> Dict[str, Any]:
        """Send RSVP confirmation email for free events (US-032)"""
        from datetime import datetime

        try:
            event_dt = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
            formatted_date = event_dt.strftime("%A, %B %d, %Y at %I:%M %p")
        except Exception:
            formatted_date = event_date

        waitlist_msg = "Great news! A spot opened up and you've been confirmed from the waitlist." if from_waitlist else ""

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            body {{font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;}}
            .header {{background-color: #8B0000; color: white; padding: 20px; text-align: center;}}
            .content {{background-color: #f9f9f9; padding: 30px;}}
            .success {{background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0;}}
            .qr-code {{text-align: center; margin: 30px 0;}}
        </style></head>
        <body>
            <div class="header"><h1>RSVP Confirmed</h1></div>
            <div class="content">
                <h2>Hi {user_name},</h2>
                <p>Your RSVP for <strong>{event_title}</strong> has been confirmed!</p>
                {f'<div class="success">{waitlist_msg}</div>' if from_waitlist else ""}
                <h3>Event Details:</h3>
                <ul>
                    <li><strong>Event:</strong> {event_title}</li>
                    <li><strong>Date & Time:</strong> {formatted_date}</li>
                    {f"<li><strong>Location:</strong> {event_location}</li>" if event_location else ""}
                    {f"<li><strong>Address:</strong> {event_address}</li>" if event_address else ""}
                </ul>
                {f'<div class="qr-code"><h3>Your Event Ticket:</h3><p>Present this QR code at check-in:</p><img src="data:image/png;base64,{qr_code}" alt="QR Code" style="max-width:300px;border:2px solid #ddd;padding:10px;"/></div>' if qr_code else ""}
                <p><small>RSVP ID: {rsvp_id}</small></p>
            </div>
        </body>
        </html>
        """

        text_body = f"Hi {user_name},\n\nYour RSVP for {event_title} is confirmed!\n\n{waitlist_msg}\n\nEvent: {event_title}\nDate: {formatted_date}\nRSVP ID: {rsvp_id}"

        return self._send_email(to_email=email, subject=f"RSVP Confirmed: {event_title}", html_body=html_body, text_body=text_body, tag="event-rsvp")

    def send_paid_event_ticket(
        self,
        email: str,
        user_name: str,
        event_title: str,
        event_date: str,
        event_location: Optional[str] = None,
        event_address: Optional[str] = None,
        amount: float = 0,
        currency: str = "USD",
        qr_code: Optional[str] = None,
        rsvp_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send ticket email for paid events (US-032)"""
        from datetime import datetime

        try:
            event_dt = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
            formatted_date = event_dt.strftime("%A, %B %d, %Y at %I:%M %p")
        except Exception:
            formatted_date = event_date

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            body {{font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;}}
            .header {{background-color: #8B0000; color: white; padding: 20px; text-align: center;}}
            .content {{background-color: #f9f9f9; padding: 30px;}}
            .qr-code {{text-align: center; margin: 30px 0;}}
        </style></head>
        <body>
            <div class="header"><h1>Your Event Ticket</h1></div>
            <div class="content">
                <h2>Hi {user_name},</h2>
                <p>Thank you for your payment! Your ticket for <strong>{event_title}</strong> is confirmed.</p>
                <h3>Payment Receipt:</h3>
                <ul>
                    <li><strong>Amount:</strong> ${amount:.2f} {currency}</li>
                    <li><strong>Event:</strong> {event_title}</li>
                    <li><strong>Date:</strong> {formatted_date}</li>
                    {f"<li><strong>Location:</strong> {event_location}</li>" if event_location else ""}
                </ul>
                {f'<div class="qr-code"><h3>Your Ticket:</h3><p>Present this QR code at check-in:</p><img src="data:image/png;base64,{qr_code}" alt="Ticket QR" style="max-width:300px;border:2px solid #ddd;padding:10px;"/></div>' if qr_code else ""}
                <p><small>Ticket ID: {rsvp_id}</small></p>
                <p><strong>Cancellation Policy:</strong> Full refund available up to 24 hours before event.</p>
            </div>
        </body>
        </html>
        """

        text_body = f"Hi {user_name},\n\nYour ticket for {event_title} is confirmed!\n\nAmount: ${amount:.2f}\nDate: {formatted_date}\nTicket ID: {rsvp_id}\n\nFull refund available up to 24 hours before event."

        return self._send_email(to_email=email, subject=f"Your Ticket: {event_title}", html_body=html_body, text_body=text_body, tag="event-ticket")

    def send_rsvp_cancellation_confirmation(
        self,
        email: str,
        user_name: str,
        event_title: str,
        event_date: str,
        refund_issued: bool = False,
        refund_amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """Send RSVP cancellation confirmation (US-032)"""
        from datetime import datetime

        try:
            event_dt = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
            formatted_date = event_dt.strftime("%A, %B %d, %Y at %I:%M %p")
        except Exception:
            formatted_date = event_date

        refund_msg = ""
        if refund_issued and refund_amount:
            refund_msg = f'<p style="color:#28a745;font-weight:bold;">Refund of ${refund_amount:.2f} issued. Allow 5-10 business days.</p>'
        elif refund_amount and not refund_issued:
            refund_msg = '<p style="color:#dc3545;">No refund - cancellation within 24 hours of event.</p>'

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            body {{font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;}}
            .header {{background-color: #8B0000; color: white; padding: 20px; text-align: center;}}
            .content {{background-color: #f9f9f9; padding: 30px;}}
        </style></head>
        <body>
            <div class="header"><h1>RSVP Canceled</h1></div>
            <div class="content">
                <h2>Hi {user_name},</h2>
                <p>Your RSVP for <strong>{event_title}</strong> on {formatted_date} has been canceled.</p>
                {refund_msg}
                <p>You can RSVP again if spots are available. We hope to see you at a future event!</p>
            </div>
        </body>
        </html>
        """

        text_body = f"Hi {user_name},\n\nYour RSVP for {event_title} on {formatted_date} has been canceled.\n\n{'Refund of $' + str(refund_amount) + ' issued.' if refund_issued else 'No refund available.' if refund_amount else ''}"

        return self._send_email(to_email=email, subject=f"RSVP Canceled: {event_title}", html_body=html_body, text_body=text_body, tag="rsvp-cancellation")

    def send_waitlist_notification(
        self,
        email: str,
        user_name: str,
        event_title: str,
        event_date: str
    ) -> Dict[str, Any]:
        """Send waitlist notification (US-032)"""
        from datetime import datetime

        try:
            event_dt = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
            formatted_date = event_dt.strftime("%A, %B %d, %Y at %I:%M %p")
        except Exception:
            formatted_date = event_date

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            body {{font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;}}
            .header {{background-color: #8B0000; color: white; padding: 20px; text-align: center;}}
            .content {{background-color: #f9f9f9; padding: 30px;}}
        </style></head>
        <body>
            <div class="header"><h1>Waitlist Confirmation</h1></div>
            <div class="content">
                <h2>Hi {user_name},</h2>
                <p>You've been added to the waitlist for <strong>{event_title}</strong> on {formatted_date}.</p>
                <p>We'll email you if a spot opens up. Spots are offered first-come, first-served.</p>
            </div>
        </body>
        </html>
        """

        text_body = f"Hi {user_name},\n\nYou're on the waitlist for {event_title} on {formatted_date}.\nWe'll notify you if a spot opens up."

        return self._send_email(to_email=email, subject=f"Waitlist: {event_title}", html_body=html_body, text_body=text_body, tag="waitlist")

    def send_waitlist_spot_available_paid(
        self,
        email: str,
        user_name: str,
        event_title: str,
        event_date: str,
        event_id: str,
        registration_fee: float
    ) -> Dict[str, Any]:
        """Send waitlist spot available notification for paid events (US-032)"""
        from datetime import datetime

        try:
            event_dt = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
            formatted_date = event_dt.strftime("%A, %B %d, %Y at %I:%M %p")
        except Exception:
            formatted_date = event_date

        from backend.config import settings
        event_url = f"{settings.PYTHON_BACKEND_URL.replace(':8000', ':3000')}/events/{event_id}"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            body {{font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;}}
            .header {{background-color: #8B0000; color: white; padding: 20px; text-align: center;}}
            .content {{background-color: #f9f9f9; padding: 30px;}}
            .cta {{text-align: center; margin: 30px 0;}}
            .button {{background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;}}
        </style></head>
        <body>
            <div class="header"><h1>Spot Available!</h1></div>
            <div class="content">
                <h2>Hi {user_name},</h2>
                <p style="color:#28a745;font-weight:bold;">Great news! A spot opened up for <strong>{event_title}</strong>!</p>
                <p><strong>Event:</strong> {event_title}<br/><strong>Date:</strong> {formatted_date}<br/><strong>Fee:</strong> ${registration_fee:.2f}</p>
                <p>You have <strong>24 hours</strong> to register and pay.</p>
                <div class="cta"><a href="{event_url}" class="button">Complete Registration</a></div>
            </div>
        </body>
        </html>
        """

        text_body = f"Hi {user_name},\n\nSpot available for {event_title} on {formatted_date}!\nFee: ${registration_fee:.2f}\n\nRegister within 24 hours: {event_url}"

        return self._send_email(to_email=email, subject=f"Spot Available: {event_title}", html_body=html_body, text_body=text_body, tag="waitlist-spot")

    def send_newsletter_confirmation(
        self,
        email: str,
        name: str,
        confirmation_url: str
    ) -> Dict[str, Any]:
        """
        Send newsletter subscription confirmation email (US-058)

        Args:
            email: Subscriber email address
            name: Subscriber name
            confirmation_url: URL to confirm subscription

        Returns:
            Postmark API response

        Raises:
            EmailSendError: If email sending fails
        """
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
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
                    background-color: #003366;
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
                    background-color: #007bff;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                    font-weight: bold;
                }}
                .button:hover {{
                    background-color: #0056b3;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                }}
                .benefits {{
                    background-color: #e8f4f8;
                    padding: 15px;
                    border-left: 4px solid #007bff;
                    margin: 20px 0;
                }}
                ul {{
                    margin: 10px 0;
                    padding-left: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Confirm Your Newsletter Subscription</h1>
            </div>
            <div class="content">
                <h2>Hi {name},</h2>
                <p>Thank you for subscribing to the WWMAA newsletter! We're excited to have you join our community of martial arts enthusiasts.</p>

                <p style="font-weight: bold; color: #003366;">Please confirm your email address by clicking the button below:</p>

                <div style="text-align: center;">
                    <a href="{confirmation_url}" class="button">Confirm Subscription</a>
                </div>

                <p style="font-size: 14px; color: #666;">
                    Or copy and paste this link into your browser:<br>
                    <a href="{confirmation_url}">{confirmation_url}</a>
                </p>

                <div class="benefits">
                    <h3 style="margin-top: 0;">What to Expect:</h3>
                    <ul>
                        <li>Latest news about martial arts events and seminars</li>
                        <li>Training tips and techniques from expert instructors</li>
                        <li>Community updates and member spotlights</li>
                        <li>Exclusive offers and early access to events</li>
                    </ul>
                </div>

                <div class="footer">
                    <p><strong>Note:</strong> This confirmation link will expire in 24 hours.</p>
                    <p>If you didn't subscribe to this newsletter, you can safely ignore this email.</p>
                    <p style="margin-top: 20px;">
                        Questions? Contact us at support@wwmaa.com<br>
                        Visit our website: <a href="https://wwmaa.com">https://wwmaa.com</a>
                    </p>
                    <p style="margin-top: 20px; font-size: 11px; color: #999;">
                        World Wide Martial Arts Association<br>
                        Privacy Policy: <a href="https://wwmaa.com/privacy">https://wwmaa.com/privacy</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Confirm Your Newsletter Subscription

        Hi {name},

        Thank you for subscribing to the WWMAA newsletter! We're excited to have you join our community.

        Please confirm your email address by clicking this link:
        {confirmation_url}

        What to Expect:
        - Latest news about martial arts events and seminars
        - Training tips and techniques from expert instructors
        - Community updates and member spotlights
        - Exclusive offers and early access to events

        Note: This confirmation link will expire in 24 hours.

        If you didn't subscribe to this newsletter, you can safely ignore this email.

        Questions? Contact us at support@wwmaa.com
        Visit our website: https://wwmaa.com

        World Wide Martial Arts Association
        Privacy Policy: https://wwmaa.com/privacy
        """

        return self._send_email(
            to_email=email,
            subject="Please confirm your newsletter subscription",
            html_body=html_body,
            text_body=text_body,
            tag="newsletter-confirmation"
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

    def send_recording_ready_email_instructor(
        self,
        email: str,
        instructor_name: str,
        session_title: str,
        session_date: str,
        duration_minutes: Optional[int] = None,
        view_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send recording ready notification to instructor (US-046)

        Args:
            email: Instructor email address
            instructor_name: Instructor name
            session_title: Training session title
            session_date: Session date
            duration_minutes: Recording duration in minutes
            view_url: URL to view the recording

        Returns:
            Postmark API response
        """
        subject = f"Recording Ready: {session_title}"

        duration_text = f" ({duration_minutes} minutes)" if duration_minutes else ""

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            body {{font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;}}
            .header {{background-color: #8B0000; color: white; padding: 20px; text-align: center;}}
            .content {{background-color: #f9f9f9; padding: 30px;}}
            .success {{background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0;}}
            .button {{display: inline-block; background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0;}}
        </style></head>
        <body>
            <div class="header"><h1>Recording Ready</h1></div>
            <div class="content">
                <h2>Hi {instructor_name},</h2>
                <div class="success">
                    <strong>Your training session recording is now available!</strong>
                </div>
                <p>The recording for your session "<strong>{session_title}</strong>" has been processed and is ready to view{duration_text}.</p>
                <p><strong>Session Date:</strong> {session_date}</p>
                <p>Members who missed the live session can now watch the recording on demand.</p>
                {f'<div style="text-align: center;"><a href="{view_url}" class="button">View Recording</a></div>' if view_url else ''}
                <p>The recording is available in your instructor dashboard and will be accessible to all registered members.</p>
            </div>
        </body>
        </html>
        """

        text_body = f"Hi {instructor_name},\n\nYour recording for '{session_title}' is ready{duration_text}!\n\nSession Date: {session_date}\n\n{f'View: {view_url}' if view_url else ''}"

        return self._send_email(
            to_email=email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            tag="recording-ready-instructor"
        )

    def send_recording_ready_email_participant(
        self,
        email: str,
        participant_name: str,
        session_title: str,
        session_date: str,
        duration_minutes: Optional[int] = None,
        view_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send recording available notification to participant (US-046)

        Args:
            email: Participant email address
            participant_name: Participant name
            session_title: Training session title
            session_date: Session date
            duration_minutes: Recording duration in minutes
            view_url: URL to view the recording

        Returns:
            Postmark API response
        """
        subject = f"Session Recording Available: {session_title}"

        duration_text = f" ({duration_minutes} minutes)" if duration_minutes else ""

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><style>
            body {{font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;}}
            .header {{background-color: #8B0000; color: white; padding: 20px; text-align: center;}}
            .content {{background-color: #f9f9f9; padding: 30px;}}
            .info {{background-color: #d1ecf1; border-left: 4px solid #17a2b8; padding: 15px; margin: 20px 0;}}
            .button {{display: inline-block; background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0;}}
        </style></head>
        <body>
            <div class="header"><h1>Recording Now Available</h1></div>
            <div class="content">
                <h2>Hi {participant_name},</h2>
                <div class="info">
                    <strong>The recording for "{session_title}" is now available to watch!</strong>
                </div>
                <p>Missed the live session or want to review the material? The full recording is now available{duration_text}.</p>
                <p><strong>Session Date:</strong> {session_date}</p>
                {f'<div style="text-align: center;"><a href="{view_url}" class="button">Watch Recording</a></div>' if view_url else ''}
                <p>Access the recording anytime from your member dashboard.</p>
            </div>
        </body>
        </html>
        """

        text_body = f"Hi {participant_name},\n\nThe recording for '{session_title}' is now available{duration_text}!\n\nSession Date: {session_date}\n\n{f'Watch: {view_url}' if view_url else ''}"

        return self._send_email(
            to_email=email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            tag="recording-ready-participant"
        )
