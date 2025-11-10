"""
Dunning Email Templates

Provides email sending functions for the dunning process.
These functions extend the EmailService with dunning-specific emails.

All emails include:
- Postmark tracking for opens and clicks
- Clear call-to-action buttons
- Timeline information
- Mobile-responsive HTML design
"""

from datetime import datetime
from typing import Dict, Any
from backend.services.email_service import EmailService, EmailSendError
from backend.config import settings


def send_payment_failed_email(
    email_service: EmailService,
    email: str,
    user_name: str,
    amount_due: float,
    currency: str,
    payment_url: str
) -> Dict[str, Any]:
    """
    Send payment failed notification (Day 0)

    Args:
        email_service: EmailService instance
        email: User's email address
        user_name: User's name for personalization
        amount_due: Amount that failed to process
        currency: Currency code
        payment_url: URL to update payment method

    Returns:
        Postmark API response

    Raises:
        EmailSendError: If email sending fails
    """
    subject = "Payment Failed - Action Required for Your WWMAA Membership"

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
            .amount {{
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
            <h1>Payment Failed</h1>
        </div>
        <div class="content">
            <h2>Hello, {user_name}</h2>

            <p>We attempted to process your WWMAA membership payment, but unfortunately it was declined.</p>

            <div class="amount">
                Amount Due: {currency} ${amount_due:.2f}
            </div>

            <div class="warning">
                <strong>Action Required:</strong> Please update your payment method to continue your membership without interruption.
            </div>

            <p>Your membership benefits will continue for now, but we need you to update your payment information within 14 days to avoid service interruption.</p>

            <div style="text-align: center;">
                <a href="{payment_url}" class="button">Update Payment Method</a>
            </div>

            <p><strong>Why did this happen?</strong></p>
            <ul>
                <li>Insufficient funds in your account</li>
                <li>Expired or incorrect card information</li>
                <li>Your bank declined the transaction</li>
                <li>Card limit reached</li>
            </ul>

            <p><strong>What happens next?</strong></p>
            <ul>
                <li>Day 3: First reminder email</li>
                <li>Day 7: Second reminder email</li>
                <li>Day 12: Final warning before cancellation</li>
                <li>Day 14: Membership canceled if payment not received</li>
            </ul>

            <p>If you have any questions or need assistance, please contact our support team at support@wwmaa.com</p>

            <p>Thank you for your prompt attention to this matter.</p>
        </div>
        <div class="footer">
            <p>Women's Martial Arts Association of America</p>
            <p>This is an automated message, please do not reply to this email.</p>
        </div>
    </body>
    </html>
    """

    text_body = f"""
    Payment Failed - Action Required

    Hello, {user_name}

    We attempted to process your WWMAA membership payment, but unfortunately it was declined.

    Amount Due: {currency} ${amount_due:.2f}

    ACTION REQUIRED: Please update your payment method to continue your membership without interruption.

    Update your payment method: {payment_url}

    Your membership benefits will continue for now, but we need you to update your payment information within 14 days to avoid service interruption.

    Why did this happen?
    - Insufficient funds in your account
    - Expired or incorrect card information
    - Your bank declined the transaction
    - Card limit reached

    What happens next?
    - Day 3: First reminder email
    - Day 7: Second reminder email
    - Day 12: Final warning before cancellation
    - Day 14: Membership canceled if payment not received

    If you have any questions or need assistance, please contact our support team at support@wwmaa.com

    ---
    Women's Martial Arts Association of America
    This is an automated message, please do not reply to this email.
    """

    return email_service._send_email(
        to_email=email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        tag="dunning-payment-failed",
        metadata={
            "user_email": email,
            "user_name": user_name,
            "amount_due": str(amount_due),
            "currency": currency,
            "dunning_stage": "payment_failed"
        }
    )


def send_dunning_first_reminder(
    email_service: EmailService,
    email: str,
    user_name: str,
    amount_due: float,
    currency: str,
    payment_url: str
) -> Dict[str, Any]:
    """
    Send first dunning reminder (Day 3)
    """
    subject = "Reminder: Update Your Payment Method - WWMAA Membership"

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
            .amount {{
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
            <h1>Payment Reminder</h1>
        </div>
        <div class="content">
            <h2>Hello, {user_name}</h2>

            <p>This is a friendly reminder that we still need to process your WWMAA membership payment.</p>

            <div class="amount">
                Amount Due: {currency} ${amount_due:.2f}
            </div>

            <div class="info">
                <strong>Your membership is still active,</strong> but we need you to update your payment method to keep it that way.
            </div>

            <p>It's quick and easy to update your payment information. Just click the button below:</p>

            <div style="text-align: center;">
                <a href="{payment_url}" class="button">Update Payment Method</a>
            </div>

            <p><strong>Timeline:</strong></p>
            <ul>
                <li>Day 0: Initial payment failure (3 days ago)</li>
                <li><strong>Day 3: Today - First reminder</strong></li>
                <li>Day 7: Second reminder</li>
                <li>Day 12: Final warning</li>
                <li>Day 14: Membership canceled if payment not updated</li>
            </ul>

            <p>We value your membership and want to ensure uninterrupted access to all WWMAA benefits.</p>

            <p>Questions? Contact us at support@wwmaa.com</p>
        </div>
        <div class="footer">
            <p>Women's Martial Arts Association of America</p>
            <p>This is an automated message, please do not reply to this email.</p>
        </div>
    </body>
    </html>
    """

    text_body = f"""
    Payment Reminder

    Hello, {user_name}

    This is a friendly reminder that we still need to process your WWMAA membership payment.

    Amount Due: {currency} ${amount_due:.2f}

    Your membership is still active, but we need you to update your payment method to keep it that way.

    Update your payment method: {payment_url}

    Timeline:
    - Day 0: Initial payment failure (3 days ago)
    - Day 3: Today - First reminder
    - Day 7: Second reminder
    - Day 12: Final warning
    - Day 14: Membership canceled if payment not updated

    We value your membership and want to ensure uninterrupted access to all WWMAA benefits.

    Questions? Contact us at support@wwmaa.com

    ---
    Women's Martial Arts Association of America
    This is an automated message, please do not reply to this email.
    """

    return email_service._send_email(
        to_email=email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        tag="dunning-first-reminder",
        metadata={
            "user_email": email,
            "user_name": user_name,
            "amount_due": str(amount_due),
            "currency": currency,
            "dunning_stage": "first_reminder"
        }
    )


def send_dunning_second_reminder(
    email_service: EmailService,
    email: str,
    user_name: str,
    amount_due: float,
    currency: str,
    payment_url: str
) -> Dict[str, Any]:
    """
    Send second dunning reminder (Day 7)
    """
    subject = "Urgent: Update Payment Method to Avoid Membership Cancellation"

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
            .urgent {{
                background-color: #f8d7da;
                border-left: 4px solid #dc3545;
                padding: 15px;
                margin: 20px 0;
            }}
            .amount {{
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
            <h1>Urgent Payment Reminder</h1>
        </div>
        <div class="content">
            <h2>Hello, {user_name}</h2>

            <p>We haven't received payment for your WWMAA membership, and time is running out.</p>

            <div class="amount">
                Amount Due: {currency} ${amount_due:.2f}
            </div>

            <div class="urgent">
                <strong>Action Required Within 7 Days:</strong> Your membership will be canceled in one week if we don't receive payment.
            </div>

            <p>Don't lose access to your membership benefits. Update your payment method now:</p>

            <div style="text-align: center;">
                <a href="{payment_url}" class="button">Update Payment Method Now</a>
            </div>

            <p><strong>Timeline:</strong></p>
            <ul>
                <li>Day 0: Initial payment failure (7 days ago)</li>
                <li>Day 3: First reminder sent</li>
                <li><strong>Day 7: Today - Second reminder (URGENT)</strong></li>
                <li>Day 12: Final warning before cancellation</li>
                <li>Day 14: Membership will be canceled</li>
            </ul>

            <p><strong>What you'll lose if canceled:</strong></p>
            <ul>
                <li>Access to members-only events and training</li>
                <li>Member directory and networking</li>
                <li>Exclusive resources and content</li>
                <li>Discounts on seminars and merchandise</li>
            </ul>

            <p>Need help? Contact us immediately at support@wwmaa.com</p>
        </div>
        <div class="footer">
            <p>Women's Martial Arts Association of America</p>
            <p>This is an automated message, please do not reply to this email.</p>
        </div>
    </body>
    </html>
    """

    text_body = f"""
    Urgent Payment Reminder

    Hello, {user_name}

    We haven't received payment for your WWMAA membership, and time is running out.

    Amount Due: {currency} ${amount_due:.2f}

    ACTION REQUIRED WITHIN 7 DAYS: Your membership will be canceled in one week if we don't receive payment.

    Update your payment method: {payment_url}

    Timeline:
    - Day 0: Initial payment failure (7 days ago)
    - Day 3: First reminder sent
    - Day 7: Today - Second reminder (URGENT)
    - Day 12: Final warning before cancellation
    - Day 14: Membership will be canceled

    What you'll lose if canceled:
    - Access to members-only events and training
    - Member directory and networking
    - Exclusive resources and content
    - Discounts on seminars and merchandise

    Need help? Contact us immediately at support@wwmaa.com

    ---
    Women's Martial Arts Association of America
    This is an automated message, please do not reply to this email.
    """

    return email_service._send_email(
        to_email=email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        tag="dunning-second-reminder",
        metadata={
            "user_email": email,
            "user_name": user_name,
            "amount_due": str(amount_due),
            "currency": currency,
            "dunning_stage": "second_reminder"
        }
    )


def send_dunning_final_warning(
    email_service: EmailService,
    email: str,
    user_name: str,
    amount_due: float,
    currency: str,
    payment_url: str
) -> Dict[str, Any]:
    """
    Send final warning before cancellation (Day 12)
    """
    subject = "FINAL WARNING: Membership Cancellation in 2 Days"

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
                background-color: #dc3545;
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
                background-color: #dc3545;
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
            .critical {{
                background-color: #f8d7da;
                border: 3px solid #dc3545;
                padding: 20px;
                margin: 20px 0;
                text-align: center;
            }}
            .countdown {{
                font-size: 36px;
                font-weight: bold;
                color: #dc3545;
                text-align: center;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>FINAL WARNING</h1>
        </div>
        <div class="content">
            <h2>Dear {user_name},</h2>

            <div class="critical">
                <div class="countdown">2 DAYS</div>
                <p style="font-size: 18px; margin: 0;"><strong>Until Your Membership Is Canceled</strong></p>
            </div>

            <p>This is your final notice. Your WWMAA membership will be canceled in 2 days if we don't receive payment.</p>

            <p style="font-size: 24px; font-weight: bold; color: #dc3545; text-align: center; margin: 20px 0;">
                Amount Due: {currency} ${amount_due:.2f}
            </p>

            <p><strong>This is your last chance to keep your membership active.</strong></p>

            <div style="text-align: center;">
                <a href="{payment_url}" class="button">UPDATE PAYMENT NOW</a>
            </div>

            <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
                <strong>What happens if you don't act:</strong>
                <ul style="margin: 10px 0;">
                    <li>Your membership will be canceled in 2 days</li>
                    <li>You'll lose all member benefits immediately</li>
                    <li>Your account will be downgraded to public status</li>
                    <li>You'll need to reapply for membership</li>
                </ul>
            </div>

            <p>If you're experiencing financial difficulties, please contact us immediately at support@wwmaa.com</p>

            <p><strong>Don't wait - Act now to preserve your membership!</strong></p>
        </div>
        <div class="footer">
            <p>Women's Martial Arts Association of America</p>
            <p>This is an automated message, please do not reply to this email.</p>
        </div>
    </body>
    </html>
    """

    text_body = f"""
    FINAL WARNING - Membership Cancellation in 2 Days

    Dear {user_name},

    ***** 2 DAYS UNTIL YOUR MEMBERSHIP IS CANCELED *****

    This is your final notice. Your WWMAA membership will be canceled in 2 days if we don't receive payment.

    Amount Due: {currency} ${amount_due:.2f}

    UPDATE PAYMENT NOW: {payment_url}

    What happens if you don't act:
    - Your membership will be canceled in 2 days
    - You'll lose all member benefits immediately
    - Your account will be downgraded to public status
    - You'll need to reapply for membership

    If you're experiencing financial difficulties, contact us immediately at support@wwmaa.com

    Don't wait - Act now to preserve your membership!

    ---
    Women's Martial Arts Association of America
    """

    return email_service._send_email(
        to_email=email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        tag="dunning-final-warning",
        metadata={
            "user_email": email,
            "user_name": user_name,
            "amount_due": str(amount_due),
            "currency": currency,
            "dunning_stage": "final_warning"
        }
    )


def send_dunning_cancellation_notice(
    email_service: EmailService,
    email: str,
    user_name: str,
    amount_due: float,
    currency: str
) -> Dict[str, Any]:
    """
    Send cancellation notice (Day 14)
    """
    subject = "Your WWMAA Membership Has Been Canceled"

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
                background-color: #6c757d;
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
                background-color: #e2e3e5;
                border-left: 4px solid #6c757d;
                padding: 15px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Membership Canceled</h1>
        </div>
        <div class="content">
            <h2>Dear {user_name},</h2>

            <p>We're sorry to inform you that your WWMAA membership has been canceled due to non-payment.</p>

            <div class="info">
                <strong>Cancellation Details:</strong><br>
                Outstanding Amount: {currency} ${amount_due:.2f}<br>
                Cancellation Date: {datetime.utcnow().strftime('%B %d, %Y')}<br>
                Reason: Payment failure after 14-day grace period
            </div>

            <p><strong>What this means:</strong></p>
            <ul>
                <li>Your access to members-only content and events has been removed</li>
                <li>Your account has been downgraded to public status</li>
                <li>You no longer have member benefits and discounts</li>
                <li>Your profile is no longer visible in the member directory</li>
            </ul>

            <p><strong>Want to rejoin?</strong></p>
            <p>We'd love to have you back! You can reactivate your membership at any time.</p>

            <div style="text-align: center;">
                <a href="{settings.PYTHON_BACKEND_URL.replace(':8000', ':3000')}/membership" class="button">Rejoin WWMAA</a>
            </div>

            <p>If you believe this cancellation was made in error, please contact support@wwmaa.com immediately.</p>

            <p>Thank you for being part of the WWMAA community. We hope to see you again soon!</p>

            <p>Best regards,<br>
            <strong>WWMAA Membership Team</strong></p>
        </div>
        <div class="footer">
            <p>Women's Martial Arts Association of America</p>
            <p>This is an automated message, but you can reply to support@wwmaa.com</p>
        </div>
    </body>
    </html>
    """

    text_body = f"""
    Membership Canceled

    Dear {user_name},

    We're sorry to inform you that your WWMAA membership has been canceled due to non-payment.

    Cancellation Details:
    Outstanding Amount: {currency} ${amount_due:.2f}
    Cancellation Date: {datetime.utcnow().strftime('%B %d, %Y')}
    Reason: Payment failure after 14-day grace period

    What this means:
    - Your access to members-only content and events has been removed
    - Your account has been downgraded to public status
    - You no longer have member benefits and discounts
    - Your profile is no longer visible in the member directory

    Want to rejoin?
    We'd love to have you back! You can reactivate your membership at any time.

    Rejoin WWMAA: {settings.PYTHON_BACKEND_URL.replace(':8000', ':3000')}/membership

    If you believe this cancellation was made in error, please contact support@wwmaa.com immediately.

    Thank you for being part of the WWMAA community. We hope to see you again soon!

    Best regards,
    WWMAA Membership Team

    ---
    Women's Martial Arts Association of America
    """

    return email_service._send_email(
        to_email=email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        tag="dunning-canceled",
        metadata={
            "user_email": email,
            "user_name": user_name,
            "amount_due": str(amount_due),
            "currency": currency,
            "dunning_stage": "canceled"
        }
    )
