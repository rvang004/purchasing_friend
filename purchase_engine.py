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
    
    async def set_quantity(self, quantity: int) -> int:
        """
        Set item quantity on product page.

        Returns the actual quantity accepted by the site — may be lower than
        requested if stock is limited. The purchase always proceeds with
        whatever the site allows.
        """
        if quantity <= 1:
            return 1
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

                    # Read back what the site actually accepted
                    actual = await element.evaluate("el => el.value")
                    try:
                        actual_qty = int(actual)
                    except (ValueError, TypeError):
                        actual_qty = quantity

                    if actual_qty < quantity:
                        logger.warning(
                            f"⚠️  Requested {quantity} but site only allows {actual_qty} "
                            f"(stock limited) — proceeding with {actual_qty}"
                        )
                    else:
                        logger.info(f"🔢 Quantity set to {actual_qty}")
                    return actual_qty

            logger.warning("⚠️  Could not find quantity input — defaulting to 1")
            return 1
        except Exception as e:
            logger.error(f"❌ Failed to set quantity: {e}")
            return 1

    async def add_to_cart(self) -> bool:
        """Add item to cart and dismiss any mini-cart popup that appears."""
        try:
            selectors = [
                'button:has-text("Add to Cart")',
                'button:has-text("Add to cart")',
                'button:has-text("Add to Basket")',
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
                    await self.page.wait_for_timeout(1500)

                    # Dismiss any "continue shopping" overlay so we aren't blocked
                    dismiss_selectors = [
                        'button:has-text("Continue shopping")',
                        'button:has-text("Continue Shopping")',
                        'button:has-text("No thanks")',
                        'button:has-text("No Thanks")',
                        '[aria-label*="close" i]',
                        '[class*="modal" i] [class*="close" i]',
                    ]
                    for d_sel in dismiss_selectors:
                        d_btn = await self.page.query_selector(d_sel)
                        if d_btn:
                            await d_btn.click()
                            await self.page.wait_for_timeout(500)
                            break

                    logger.info("✅ Item added to cart")
                    return True

            logger.warning("⚠️  Could not find 'Add to Cart' button")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to add to cart: {e}")
            return False

    async def navigate_to_cart(self) -> bool:
        """
        Land on the cart page before attempting checkout.

        First tries mini-cart "Go to Cart" links, then falls back to
        common cart URL patterns so the checkout button is always reachable.
        """
        try:
            # Mini-cart / confirmation popup links
            cart_link_selectors = [
                'a:has-text("Go to Cart")',
                'a:has-text("View Cart")',
                'a:has-text("View cart")',
                'button:has-text("Go to Cart")',
                'button:has-text("View Cart")',
                '[class*="cart" i] a[href*="cart" i]',
            ]
            for sel in cart_link_selectors:
                link = await self.page.query_selector(sel)
                if link:
                    await link.click()
                    await self.page.wait_for_load_state("networkidle")
                    logger.info("🛒 Navigated to cart via mini-cart link")
                    return True

            # Fall back: derive cart URL from current site
            current_url = self.page.url
            cart_paths = ["/cart", "/basket", "/bag", "/checkout/cart"]
            import urllib.parse
            parsed = urllib.parse.urlparse(current_url)
            base = f"{parsed.scheme}://{parsed.netloc}"

            for path in cart_paths:
                cart_url = base + path
                try:
                    resp = await self.page.goto(cart_url, wait_until="networkidle")
                    if resp and resp.ok:
                        logger.info(f"🛒 Navigated to cart via {cart_url}")
                        return True
                except Exception:
                    continue

            logger.warning("⚠️  Could not navigate to cart page")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to navigate to cart: {e}")
            return False
    
    async def select_shipping_address(self, address: dict = None) -> bool:
        """
        Confirm the shipping address at checkout.

        If `address` is None: click the default/first saved address on the page.
        If `address` has data: fill in the address form fields.
        """
        try:
            # --- Case 1: site has saved addresses, click the default one ---
            saved_address_selectors = [
                'input[type="radio"][name*="address" i]:first-of-type',
                '[class*="address-book" i] input[type="radio"]:first-of-type',
            ]
            confirm_selectors = [
                'button:has-text("Deliver to this address")',
                'button:has-text("Use this address")',
                'button:has-text("Ship to this address")',
                'button:has-text("Deliver here")',
                '[class*="ship-to" i] button',
                '[class*="address" i] button[type="submit"]',
            ]

            for sel in confirm_selectors:
                btn = await self.page.query_selector(sel)
                if btn:
                    if self.dry_run:
                        logger.info("🔄 DRY RUN: Would confirm default shipping address")
                        return True
                    await btn.click()
                    await self.page.wait_for_load_state("networkidle")
                    logger.info("✅ Default shipping address confirmed")
                    return True

            # Try selecting the first radio option then confirming
            for sel in saved_address_selectors:
                radio = await self.page.query_selector(sel)
                if radio:
                    await radio.click()
                    for confirm_sel in confirm_selectors:
                        btn = await self.page.query_selector(confirm_sel)
                        if btn:
                            if self.dry_run:
                                logger.info("🔄 DRY RUN: Would confirm saved address")
                                return True
                            await btn.click()
                            await self.page.wait_for_load_state("networkidle")
                            logger.info("✅ Saved address selected and confirmed")
                            return True

            # --- Case 2: no saved address found, fill in form fields ---
            if address:
                field_map = [
                    ('input[name*="fullName" i], input[name*="full_name" i], input[name*="name" i]',
                     address.get("full_name", "")),
                    ('input[name*="address1" i], input[name*="line1" i], input[id*="addressLine1" i]',
                     address.get("line1", "")),
                    ('input[name*="address2" i], input[name*="line2" i], input[id*="addressLine2" i]',
                     address.get("line2", "")),
                    ('input[name*="city" i], input[id*="city" i]',
                     address.get("city", "")),
                    ('input[name*="state" i], select[name*="state" i]',
                     address.get("state", "")),
                    ('input[name*="zip" i], input[name*="postal" i], input[id*="zipCode" i]',
                     address.get("zip_code", "")),
                ]
                filled = 0
                for selector, value in field_map:
                    if not value:
                        continue
                    el = await self.page.query_selector(selector)
                    if el:
                        tag = await el.evaluate("el => el.tagName.toLowerCase()")
                        if tag == "select":
                            await el.select_option(value)
                        else:
                            await el.triple_click()
                            await el.type(value)
                        filled += 1

                if filled:
                    logger.info(f"✅ Filled {filled} address field(s) from stored address")
                    return True

            # Nothing matched — site likely auto-applies the default, proceed
            logger.info("ℹ️  No address picker found — site will use its saved default")
            return True

        except Exception as e:
            logger.error(f"❌ Error selecting shipping address: {e}")
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

            # Set quantity — returns actual qty site accepted (may be < requested if low stock)
            actual_quantity = await self.set_quantity(quantity)
            result["quantity"] = actual_quantity

            # Get item price and check against limit
            item_price = await self.get_item_price()
            result["item_price"] = item_price

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

            # Add to cart (handles mini-cart popups automatically)
            if not await self.add_to_cart():
                result["error"] = "Failed to add to cart"
                return result

            # Navigate to cart page so the checkout button is reachable
            if not await self.navigate_to_cart():
                result["error"] = "Failed to reach cart page"
                return result

            # Checkout
            if not await self.checkout():
                result["error"] = "Checkout failed"
                return result

            # Select / confirm shipping address
            await self.select_shipping_address(account.get("shipping_address"))

            # Complete purchase
            if not await self.complete_purchase():
                result["error"] = "Failed to complete purchase"
                return result

            result["success"] = True
            logger.info(
                f"🎉 Purchase successful for {account.get('id')} — "
                f"qty: {actual_quantity}, price: ${item_price}"
            )
            
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
