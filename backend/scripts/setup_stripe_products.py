#!/usr/bin/env python3
"""
Stripe Product & Price Setup Script for WWMAA

This script creates products and prices in Stripe for WWMAA membership tiers:
- Basic Membership: $29/year
- Premium Membership: $79/year
- Instructor Membership: $149/year

Usage:
    python setup_stripe_products.py [--mode test|live] [--force]

Arguments:
    --mode: Stripe mode (test or live, default: test)
    --force: Force recreate products if they already exist

Requirements (US-021):
- Creates products for all three membership tiers
- Sets annual billing cycle
- Stores product/price IDs for reference
- Idempotent operation (can be run multiple times safely)
"""

import argparse
import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import stripe
from backend.config import settings

# ============================================================================
# MEMBERSHIP TIER CONFIGURATION (US-021)
# ============================================================================

MEMBERSHIP_TIERS = {
    "basic": {
        "name": "Basic Membership",
        "price_annual": 2900,  # $29.00 in cents
        "currency": "usd",
        "description": "Basic WWMAA membership with access to member directory and events",
        "features": [
            "Access to member directory",
            "Event registration",
            "Monthly newsletter",
            "Basic training resources"
        ],
        "metadata": {
            "tier": "basic",
            "billing_cycle": "annual",
            "category": "membership"
        }
    },
    "premium": {
        "name": "Premium Membership",
        "price_annual": 7900,  # $79.00 in cents
        "currency": "usd",
        "description": "Premium membership with enhanced features and priority support",
        "features": [
            "All Basic features",
            "Priority event registration",
            "Exclusive training videos",
            "Priority support",
            "Member discounts (10% off events)"
        ],
        "metadata": {
            "tier": "premium",
            "billing_cycle": "annual",
            "category": "membership"
        }
    },
    "instructor": {
        "name": "Instructor Membership",
        "price_annual": 14900,  # $149.00 in cents
        "currency": "usd",
        "description": "Instructor membership with full access to training materials and certification",
        "features": [
            "All Premium features",
            "Instructor certification access",
            "Advanced training materials",
            "Teaching resources",
            "Instructor directory listing",
            "Member discounts (20% off events)"
        ],
        "metadata": {
            "tier": "instructor",
            "billing_cycle": "annual",
            "category": "membership"
        }
    }
}


# ============================================================================
# STRIPE PRODUCT SETUP
# ============================================================================

class StripeProductSetup:
    """
    Setup Stripe products and prices for WWMAA membership tiers
    """

    def __init__(self, mode: str = "test", force: bool = False):
        """
        Initialize Stripe product setup

        Args:
            mode: Stripe mode ("test" or "live")
            force: Force recreate products if they already exist
        """
        self.mode = mode
        self.force = force
        self.results = {
            "mode": mode,
            "products": {},
            "prices": {},
            "errors": []
        }

        # Configure Stripe API key based on mode
        if mode == "test":
            stripe.api_key = settings.STRIPE_SECRET_KEY
            if not stripe.api_key.startswith("sk_test_"):
                raise ValueError(
                    "STRIPE_SECRET_KEY must be a test key (sk_test_...) when mode is 'test'"
                )
        else:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            if not stripe.api_key.startswith("sk_live_"):
                print("WARNING: Using live mode. This will create real products in Stripe!")
                response = input("Continue? (yes/no): ")
                if response.lower() != "yes":
                    print("Aborted.")
                    sys.exit(0)

        print(f"\n{'='*70}")
        print(f"Stripe Product Setup - {mode.upper()} mode")
        print(f"{'='*70}\n")

    def find_existing_product(self, tier_name: str) -> Optional[Dict]:
        """
        Find existing product by name

        Args:
            tier_name: Product name to search for

        Returns:
            Product object if found, None otherwise
        """
        try:
            products = stripe.Product.list(limit=100)
            for product in products.data:
                if product.name == tier_name:
                    return product
            return None
        except stripe.error.StripeError as e:
            print(f"Error searching for product '{tier_name}': {e}")
            return None

    def find_existing_price(self, product_id: str) -> Optional[Dict]:
        """
        Find existing price for a product

        Args:
            product_id: Stripe product ID

        Returns:
            Price object if found, None otherwise
        """
        try:
            prices = stripe.Price.list(product=product_id, limit=10)
            if prices.data:
                # Return the first active price
                for price in prices.data:
                    if price.active:
                        return price
            return None
        except stripe.error.StripeError as e:
            print(f"Error searching for prices for product '{product_id}': {e}")
            return None

    def create_product(
        self,
        tier_id: str,
        tier_config: Dict
    ) -> Optional[Dict]:
        """
        Create a Stripe product

        Args:
            tier_id: Tier identifier (basic, premium, instructor)
            tier_config: Tier configuration dictionary

        Returns:
            Created product object or None if failed
        """
        try:
            print(f"\nCreating product: {tier_config['name']}")
            print(f"  Description: {tier_config['description']}")

            # Check if product already exists
            existing_product = self.find_existing_product(tier_config['name'])

            if existing_product and not self.force:
                print(f"  → Product already exists: {existing_product.id}")
                print(f"     Use --force to recreate")
                return existing_product

            if existing_product and self.force:
                print(f"  → Archiving existing product: {existing_product.id}")
                stripe.Product.modify(existing_product.id, active=False)

            # Create product
            product = stripe.Product.create(
                name=tier_config['name'],
                description=tier_config['description'],
                metadata=tier_config['metadata']
            )

            print(f"  ✓ Product created: {product.id}")
            return product

        except stripe.error.StripeError as e:
            error_msg = f"Failed to create product '{tier_config['name']}': {e}"
            print(f"  ✗ {error_msg}")
            self.results['errors'].append(error_msg)
            return None

    def create_price(
        self,
        tier_id: str,
        tier_config: Dict,
        product_id: str
    ) -> Optional[Dict]:
        """
        Create a Stripe price for a product

        Args:
            tier_id: Tier identifier (basic, premium, instructor)
            tier_config: Tier configuration dictionary
            product_id: Stripe product ID

        Returns:
            Created price object or None if failed
        """
        try:
            amount = tier_config['price_annual']
            currency = tier_config['currency']

            print(f"\nCreating price for {tier_config['name']}")
            print(f"  Amount: ${amount/100:.2f} {currency.upper()}")
            print(f"  Billing: Annual")

            # Check if price already exists
            existing_price = self.find_existing_price(product_id)

            if existing_price and not self.force:
                print(f"  → Price already exists: {existing_price.id}")
                print(f"     Use --force to recreate")
                return existing_price

            if existing_price and self.force:
                print(f"  → Archiving existing price: {existing_price.id}")
                stripe.Price.modify(existing_price.id, active=False)

            # Create price with annual billing cycle (US-021 requirement)
            price = stripe.Price.create(
                product=product_id,
                unit_amount=amount,
                currency=currency,
                recurring={
                    "interval": "year",  # Annual billing per US-021
                    "interval_count": 1
                },
                metadata={
                    "tier": tier_id,
                    "billing_cycle": "annual"
                }
            )

            print(f"  ✓ Price created: {price.id}")
            return price

        except stripe.error.StripeError as e:
            error_msg = f"Failed to create price for '{tier_config['name']}': {e}"
            print(f"  ✗ {error_msg}")
            self.results['errors'].append(error_msg)
            return None

    def setup_all_tiers(self) -> Dict:
        """
        Setup all membership tier products and prices

        Returns:
            Dictionary with setup results
        """
        print("\nSetting up membership tiers...")
        print(f"{'='*70}\n")

        for tier_id, tier_config in MEMBERSHIP_TIERS.items():
            # Create product
            product = self.create_product(tier_id, tier_config)

            if product:
                self.results['products'][tier_id] = {
                    "id": product.id,
                    "name": product.name,
                    "description": product.description
                }

                # Create price
                price = self.create_price(tier_id, tier_config, product.id)

                if price:
                    self.results['prices'][tier_id] = {
                        "id": price.id,
                        "amount": tier_config['price_annual'],
                        "currency": tier_config['currency'],
                        "interval": "year"
                    }

        return self.results

    def save_results(self, output_file: Optional[str] = None) -> None:
        """
        Save setup results to a JSON file

        Args:
            output_file: Path to output file (default: stripe_products_{mode}.json)
        """
        if output_file is None:
            output_file = f"stripe_products_{self.mode}.json"

        output_path = Path(__file__).parent / output_file

        try:
            with open(output_path, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"\n✓ Results saved to: {output_path}")
        except Exception as e:
            print(f"\n✗ Failed to save results: {e}")

    def print_summary(self) -> None:
        """Print setup summary"""
        print(f"\n{'='*70}")
        print("Setup Summary")
        print(f"{'='*70}\n")

        print(f"Mode: {self.results['mode'].upper()}")
        print(f"Products created: {len(self.results['products'])}")
        print(f"Prices created: {len(self.results['prices'])}")

        if self.results['errors']:
            print(f"\nErrors encountered: {len(self.results['errors'])}")
            for error in self.results['errors']:
                print(f"  - {error}")
        else:
            print("\n✓ All products and prices created successfully!")

        if self.results['products']:
            print("\nProduct & Price IDs:")
            for tier_id in MEMBERSHIP_TIERS.keys():
                if tier_id in self.results['products']:
                    product = self.results['products'][tier_id]
                    price = self.results['prices'].get(tier_id, {})
                    print(f"\n  {tier_id.upper()}:")
                    print(f"    Product ID: {product['id']}")
                    if price:
                        print(f"    Price ID:   {price['id']}")
                        print(f"    Amount:     ${price['amount']/100:.2f}/{price['interval']}")

        print(f"\n{'='*70}\n")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Setup Stripe products and prices for WWMAA membership tiers"
    )
    parser.add_argument(
        "--mode",
        choices=["test", "live"],
        default="test",
        help="Stripe mode (test or live, default: test)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreate products if they already exist"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path for results (default: stripe_products_{mode}.json)"
    )

    args = parser.parse_args()

    try:
        # Initialize setup
        setup = StripeProductSetup(mode=args.mode, force=args.force)

        # Setup all tiers
        results = setup.setup_all_tiers()

        # Print summary
        setup.print_summary()

        # Save results
        setup.save_results(output_file=args.output)

        # Exit with error code if there were errors
        if results['errors']:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
