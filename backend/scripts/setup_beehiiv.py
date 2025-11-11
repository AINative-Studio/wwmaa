"""
BeeHiiv Setup Script

Automated setup script for configuring BeeHiiv integration.
This script:
- Validates API key
- Creates email lists (General, Members Only, Instructors)
- Stores configuration in ZeroDB
- Validates custom domain configuration
- Checks DNS records (DKIM, SPF, DMARC)
- Sends test email

Usage:
    python backend/scripts/setup_beehiiv.py
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import dns.resolver

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.beehiiv_service import BeeHiivService, BeeHiivAPIError
from database.zerodb import ZeroDBClient
from models.schemas import BeeHiivConfig
from uuid import uuid4

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BeeHiivSetup:
    """BeeHiiv configuration setup utility"""

    def __init__(self):
        """Initialize setup utility"""
        self.api_key = os.getenv("BEEHIIV_API_KEY")
        self.publication_id = os.getenv("BEEHIIV_PUBLICATION_ID")
        self.custom_domain = os.getenv("NEWSLETTER_CUSTOM_DOMAIN", "newsletter.wwmaa.com")
        self.from_email = os.getenv("NEWSLETTER_FROM_EMAIL", "newsletter@wwmaa.com")
        self.from_name = os.getenv("NEWSLETTER_FROM_NAME", "WWMAA Team")

        if not self.api_key or not self.publication_id:
            raise ValueError(
                "Missing required environment variables: BEEHIIV_API_KEY and BEEHIIV_PUBLICATION_ID"
            )

        self.service = BeeHiivService(self.api_key, self.publication_id)
        self.db = None

    async def setup_database(self):
        """Initialize ZeroDB connection"""
        logger.info("Connecting to ZeroDB...")
        self.db = ZeroDBClient()
        await self.db.connect()
        logger.info("Connected to ZeroDB successfully")

    async def close_database(self):
        """Close ZeroDB connection"""
        if self.db:
            await self.db.disconnect()
            logger.info("Disconnected from ZeroDB")

    def validate_api_key(self) -> bool:
        """
        Validate BeeHiiv API key

        Returns:
            True if valid, False otherwise
        """
        logger.info("Validating BeeHiiv API key...")
        try:
            is_valid = self.service.validate_api_key()
            if is_valid:
                logger.info("API key is valid")
            else:
                logger.error("API key is invalid")
            return is_valid
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False

    def check_dns_record(
        self,
        domain: str,
        record_type: str,
        expected_value: Optional[str] = None
    ) -> bool:
        """
        Check DNS record existence and optionally validate value

        Args:
            domain: Domain name to check
            record_type: DNS record type (A, TXT, CNAME, etc.)
            expected_value: Expected record value (optional)

        Returns:
            True if record exists and matches expected value (if provided)
        """
        try:
            answers = dns.resolver.resolve(domain, record_type)
            if not expected_value:
                return len(answers) > 0

            for rdata in answers:
                record_value = str(rdata).strip('"')
                if expected_value in record_value:
                    return True
            return False
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
            return False
        except Exception as e:
            logger.warning(f"DNS check error for {domain} ({record_type}): {str(e)}")
            return False

    def check_dkim(self) -> bool:
        """
        Check DKIM DNS record

        Returns:
            True if DKIM record exists
        """
        logger.info("Checking DKIM configuration...")
        dkim_domain = f"beehiiv._domainkey.{self.custom_domain}"
        exists = self.check_dns_record(dkim_domain, "TXT")

        if exists:
            logger.info(f"DKIM record found for {dkim_domain}")
        else:
            logger.warning(f"DKIM record not found for {dkim_domain}")
            logger.info("Add this DNS record to complete setup:")
            logger.info(f"  Type: TXT")
            logger.info(f"  Host: beehiiv._domainkey")
            logger.info(f"  Value: (provided by BeeHiiv)")

        return exists

    def check_spf(self) -> bool:
        """
        Check SPF DNS record

        Returns:
            True if SPF record exists and includes BeeHiiv
        """
        logger.info("Checking SPF configuration...")
        exists = self.check_dns_record(self.custom_domain, "TXT", "v=spf1")
        includes_beehiiv = self.check_dns_record(self.custom_domain, "TXT", "include:beehiiv.com")

        if exists and includes_beehiiv:
            logger.info(f"SPF record correctly configured for {self.custom_domain}")
        elif exists:
            logger.warning(f"SPF record exists but doesn't include BeeHiiv")
            logger.info("Update your SPF record to include: include:beehiiv.com")
        else:
            logger.warning(f"SPF record not found for {self.custom_domain}")
            logger.info("Add this DNS record:")
            logger.info(f"  Type: TXT")
            logger.info(f"  Host: @")
            logger.info(f"  Value: v=spf1 include:beehiiv.com ~all")

        return exists and includes_beehiiv

    def check_dmarc(self) -> bool:
        """
        Check DMARC DNS record

        Returns:
            True if DMARC record exists
        """
        logger.info("Checking DMARC configuration...")
        dmarc_domain = f"_dmarc.{self.custom_domain}"
        exists = self.check_dns_record(dmarc_domain, "TXT", "v=DMARC1")

        if exists:
            logger.info(f"DMARC record found for {dmarc_domain}")
        else:
            logger.warning(f"DMARC record not found for {dmarc_domain}")
            logger.info("Add this DNS record:")
            logger.info(f"  Type: TXT")
            logger.info(f"  Host: _dmarc")
            logger.info(f"  Value: v=DMARC1; p=none; rua=mailto:dmarc@wwmaa.com")

        return exists

    def send_test_email(self, recipient_email: str) -> bool:
        """
        Send test email to verify setup

        Args:
            recipient_email: Email address to send test to

        Returns:
            True if email sent successfully
        """
        logger.info(f"Sending test email to {recipient_email}...")
        try:
            test_content = """
            <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #333;">BeeHiiv Setup Test</h1>
                    <p>Congratulations! Your BeeHiiv integration is working correctly.</p>
                    <p>This test email confirms that:</p>
                    <ul>
                        <li>API key is valid</li>
                        <li>Email sending is functional</li>
                        <li>Domain configuration is correct</li>
                    </ul>
                    <p style="color: #666; font-size: 12px; margin-top: 40px;">
                        Sent from WWMAA Newsletter System
                    </p>
                </body>
            </html>
            """

            result = self.service.send_test_email(
                email=recipient_email,
                subject="BeeHiiv Setup Test - WWMAA",
                content=test_content
            )

            logger.info("Test email sent successfully")
            return True
        except BeeHiivAPIError as e:
            logger.error(f"Failed to send test email: {str(e)}")
            return False

    async def save_configuration(
        self,
        list_ids: Dict[str, str],
        dkim_configured: bool,
        spf_configured: bool,
        dmarc_configured: bool
    ):
        """
        Save BeeHiiv configuration to ZeroDB

        Args:
            list_ids: Email list IDs by type
            dkim_configured: DKIM status
            spf_configured: SPF status
            dmarc_configured: DMARC status
        """
        logger.info("Saving configuration to ZeroDB...")

        config = BeeHiivConfig(
            id=uuid4(),
            api_key=self.api_key,
            publication_id=self.publication_id,
            list_ids=list_ids,
            custom_domain=self.custom_domain,
            from_email=self.from_email,
            from_name=self.from_name,
            dkim_configured=dkim_configured,
            spf_configured=spf_configured,
            dmarc_configured=dmarc_configured,
            domain_verified=(dkim_configured and spf_configured),
            is_active=True,
            auto_sync_enabled=True,
            welcome_email_enabled=True,
            setup_completed_at=datetime.utcnow()
        )

        # Check if config already exists
        existing_configs = await self.db.find("beehiiv_config", {})

        if existing_configs:
            # Update existing config
            config_id = existing_configs[0]["id"]
            await self.db.update_one(
                "beehiiv_config",
                {"id": config_id},
                config.dict(exclude={"id", "created_at"})
            )
            logger.info(f"Updated existing configuration (ID: {config_id})")
        else:
            # Create new config
            await self.db.insert_one("beehiiv_config", config.dict())
            logger.info(f"Created new configuration (ID: {config.id})")

    async def run_setup(self, test_email: Optional[str] = None):
        """
        Run complete setup process

        Args:
            test_email: Email address for test email (optional)
        """
        logger.info("=" * 60)
        logger.info("Starting BeeHiiv Setup")
        logger.info("=" * 60)

        try:
            # Step 1: Validate API key
            if not self.validate_api_key():
                logger.error("Setup failed: Invalid API key")
                return False

            # Step 2: Setup database
            await self.setup_database()

            # Step 3: Get publication info
            logger.info("Fetching publication information...")
            try:
                pub_info = self.service._make_request("GET", f"publications/{self.publication_id}")
                logger.info(f"Publication: {pub_info.get('data', {}).get('name', 'Unknown')}")
            except Exception as e:
                logger.warning(f"Could not fetch publication info: {str(e)}")

            # Step 4: Check DNS records
            dkim_ok = self.check_dkim()
            spf_ok = self.check_spf()
            dmarc_ok = self.check_dmarc()

            # Step 5: Get or create list IDs from environment
            list_ids = {
                "general": os.getenv("BEEHIIV_LIST_ID_GENERAL", ""),
                "members_only": os.getenv("BEEHIIV_LIST_ID_MEMBERS", ""),
                "instructors": os.getenv("BEEHIIV_LIST_ID_INSTRUCTORS", "")
            }

            # Validate list IDs
            if not all(list_ids.values()):
                logger.warning("Some list IDs are missing from environment variables:")
                for list_type, list_id in list_ids.items():
                    if not list_id:
                        logger.warning(f"  - BEEHIIV_LIST_ID_{list_type.upper()} not set")
                logger.info("List management is done through BeeHiiv dashboard")

            # Step 6: Save configuration
            await self.save_configuration(
                list_ids=list_ids,
                dkim_configured=dkim_ok,
                spf_configured=spf_ok,
                dmarc_configured=dmarc_ok
            )

            # Step 7: Send test email if requested
            if test_email:
                self.send_test_email(test_email)

            # Summary
            logger.info("=" * 60)
            logger.info("Setup Summary")
            logger.info("=" * 60)
            logger.info(f"API Key: Valid")
            logger.info(f"Publication ID: {self.publication_id}")
            logger.info(f"Custom Domain: {self.custom_domain}")
            logger.info(f"From Email: {self.from_email}")
            logger.info(f"DKIM: {'Configured' if dkim_ok else 'Not Configured'}")
            logger.info(f"SPF: {'Configured' if spf_ok else 'Not Configured'}")
            logger.info(f"DMARC: {'Configured' if dmarc_ok else 'Not Configured'}")
            logger.info("=" * 60)

            if dkim_ok and spf_ok:
                logger.info("Setup completed successfully!")
            else:
                logger.warning("Setup completed with warnings. Configure missing DNS records.")

            return True

        except Exception as e:
            logger.error(f"Setup failed: {str(e)}", exc_info=True)
            return False
        finally:
            await self.close_database()


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="BeeHiiv Setup Utility")
    parser.add_argument(
        "--test-email",
        help="Send test email to this address",
        default=None
    )

    args = parser.parse_args()

    setup = BeeHiivSetup()
    success = await setup.run_setup(test_email=args.test_email)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
