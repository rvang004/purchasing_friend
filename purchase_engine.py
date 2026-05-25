"""
Purchase automation engine using Playwright.
Handles login, item selection, and checkout across multiple e-commerce sites.
"""

import asyncio
from playwright.async_api import async_playwright, Page, Browser
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PurchaseEngine:
    """Automated purchase executor."""
    
    def __init__(self, headless: bool = True, dry_run: bool = False):
        self.headless = headless
        self.dry_run = dry_run
        self.browser: Browser = None
        self.page: Page = None
    
    async def initialize(self):
        """Start browser instance."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        logger.info("✅ Browser initialized")
    
    async def close(self):
        """Close browser."""
        if self.browser:
            await self.browser.close()
        logger.info("🛑 Browser closed")
    
    async def login(self, site_url: str, email: str, password: str) -> bool:
        """
        Generic login handler. Adapts based on site detected.
        Override for specific sites in subclasses.
        """
        try:
            await self.page.goto(site_url, wait_until="networkidle")
            logger.info(f"📍 Navigated to {site_url}")
            
            # Try to find email/password fields (generic approach)
            email_input = await self.page.query_selector('input[type="email"], input[name*="email" i]')
            if not email_input:
                logger.warning("❌ Could not find email input on this site")
                return False
            
            await email_input.fill(email)
            await self.page.wait_for_timeout(500)
            
            password_input = await self.page.query_selector('input[type="password"]')
            if not password_input:
                logger.warning("❌ Could not find password input")
                return False
            
            await password_input.fill(password)
            
            # Submit form
            submit_btn = await self.page.query_selector('button[type="submit"]')
            if submit_btn:
                await submit_btn.click()
                await self.page.wait_for_load_state("networkidle")
                logger.info("✅ Login successful")
                return True
            
            return False
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            return False
    
    async def navigate_to_product(self, product_url: str) -> bool:
        """Navigate to product URL."""
        try:
            await self.page.goto(product_url, wait_until="networkidle")
            logger.info(f"📍 Product page loaded: {product_url}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to navigate to product: {e}")
            return False
    
    async def get_item_price(self) -> float:
        """Extract item price from product page (generic selector)."""
        try:
            # Try common price selectors
            price_selectors = [
                '[class*="price" i]',
                '[class*="Price" i]',
                '[id*="price" i]',
                'span[class*="price" i]',
                'div[class*="price" i]',
                '[class*="amount" i]',
                '[class*="cost" i]',
            ]
            
            price_text = None
            for selector in price_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    price_text = await element.inner_text()
                    break
            
            if not price_text:
                logger.warning("⚠️  Could not find price on this page")
                return None
            
            # Clean price text (remove $, commas, etc.)
            import re
            price_match = re.search(r'\d+\.?\d*', price_text.replace(',', ''))
            if price_match:
                price = float(price_match.group())
                logger.info(f"💰 Detected item price: ${price}")
                return price
            
            logger.warning(f"⚠️  Could not parse price from: {price_text}")
            return None
        except Exception as e:
            logger.error(f"❌ Error getting price: {e}")
            return None
    
    async def set_quantity(self, quantity: int) -> bool:
        """Set item quantity on product page (generic selector)."""
        if quantity <= 1:
            return True  # default is usually 1, nothing to do
        try:
            qty_selectors = [
                'select[name*="quantity" i]',
                'input[name*="quantity" i]',
                'input[id*="quantity" i]',
                'input[aria-label*="quantity" i]',
            ]
            for selector in qty_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    tag = await element.evaluate("el => el.tagName.toLowerCase()")
                    if tag == "select":
                        await element.select_option(str(quantity))
                    else:
                        await element.triple_click()
                        await element.type(str(quantity))
                    logger.info(f"🔢 Quantity set to {quantity}")
                    return True
            logger.warning("⚠️  Could not find quantity input — defaulting to 1")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to set quantity: {e}")
            return False

    async def add_to_cart(self) -> bool:
        """Add item to cart (generic selector)."""
        try:
            # Try common selectors for "Add to Cart" button
            selectors = [
                'button:has-text("Add to Cart")',
                'button:has-text("Add to cart")',
                'button[class*="add-to-cart" i]',
                '[class*="add-to-cart" i]',
            ]
            
            for selector in selectors:
                btn = await self.page.query_selector(selector)
                if btn:
                    if self.dry_run:
                        logger.info("🔄 DRY RUN: Would click 'Add to Cart'")
                        return True
                    
                    await btn.click()
                    await self.page.wait_for_timeout(1000)
                    logger.info("✅ Item added to cart")
                    return True
            
            logger.warning("⚠️  Could not find 'Add to Cart' button")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to add to cart: {e}")
            return False
    
    async def checkout(self) -> bool:
        """Proceed to checkout."""
        try:
            selectors = [
                'button:has-text("Checkout")',
                'button:has-text("Proceed to Checkout")',
                'a:has-text("Checkout")',
                '[class*="checkout" i]'
            ]
            
            for selector in selectors:
                btn = await self.page.query_selector(selector)
                if btn:
                    if self.dry_run:
                        logger.info("🔄 DRY RUN: Would proceed to checkout")
                        return True
                    
                    await btn.click()
                    await self.page.wait_for_load_state("networkidle")
                    logger.info("✅ Proceeded to checkout")
                    return True
            
            logger.warning("⚠️  Could not find checkout button")
            return False
        except Exception as e:
            logger.error(f"❌ Checkout failed: {e}")
            return False
    
    async def complete_purchase(self) -> bool:
        """Click final purchase/place order button."""
        try:
            selectors = [
                'button:has-text("Place Order")',
                'button:has-text("Complete Purchase")',
                'button:has-text("Confirm Order")',
                'button:has-text("Buy Now")',
            ]
            
            for selector in selectors:
                btn = await self.page.query_selector(selector)
                if btn:
                    if self.dry_run:
                        logger.info("🔄 DRY RUN: Would complete purchase")
                        return True
                    
                    await btn.click()
                    await self.page.wait_for_load_state("networkidle")
                    logger.info("✅ Purchase completed!")
                    return True
            
            logger.warning("⚠️  Could not find purchase confirmation button")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to complete purchase: {e}")
            return False
    
    async def execute_purchase(self, account: dict, product_url: str, quantity: int = 1) -> dict:
        """Execute full purchase flow."""
        result = {
            "success": False,
            "account_id": account.get("id"),
            "product_url": product_url,
            "timestamp": datetime.now().isoformat(),
            "error": None,
            "item_price": None
        }
        
        try:
            # Login
            if not await self.login(account["site"], account["email"], account["password"]):
                result["error"] = "Login failed"
                return result
            
            # Navigate to product
            if not await self.navigate_to_product(product_url):
                result["error"] = "Failed to navigate to product"
                return result

            # Set quantity before adding to cart
            await self.set_quantity(quantity)
            
            # Get item price and check against limit
            item_price = await self.get_item_price()
            result["item_price"] = item_price
            
            # Check if price limit is enabled
            price_limit_enabled = account.get("price_limit_enabled", True)
            price_limit = account.get("price_limit_per_item")
            
            if price_limit_enabled and price_limit and item_price:
                if item_price > price_limit:
                    result["error"] = f"Item price (${item_price}) exceeds limit (${price_limit})"
                    logger.warning(f"⚠️  {result['error']}")
                    return result
            elif item_price is None and price_limit_enabled:
                logger.warning("⚠️  Could not detect price, proceeding with caution")
            elif not price_limit_enabled:
                logger.info("🔓 Price limit disabled for this account, skipping price check")
            
            # Add to cart
            if not await self.add_to_cart():
                result["error"] = "Failed to add to cart"
                return result
            
            # Checkout
            if not await self.checkout():
                result["error"] = "Checkout failed"
                return result
            
            # Complete purchase
            if not await self.complete_purchase():
                result["error"] = "Failed to complete purchase"
                return result
            
            result["success"] = True
            logger.info(f"🎉 Purchase successful for {account.get('id')} (${item_price})")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Unexpected error: {e}")
        
        return result


async def run_purchase(account: dict, product_url: str, quantity: int = 1, dry_run: bool = False) -> dict:
    """Standalone function to execute a single purchase."""
    engine = PurchaseEngine(headless=True, dry_run=dry_run)

    try:
        await engine.initialize()
        result = await engine.execute_purchase(account, product_url, quantity=quantity)
        return result
    finally:
        await engine.close()
