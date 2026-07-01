"""Generic browser actions for purchase automation.

These are deliberately generic and should eventually become site adapters.
For now, they keep selector goblins out of the orchestration engine.
"""

from __future__ import annotations

import logging
import re
import urllib.parse
from typing import Any

logger = logging.getLogger(__name__)


async def login(page: Any, site_url: str, email: str, password: str) -> bool:
    try:
        await page.goto(site_url, wait_until="networkidle")
        logger.info("Navigated to %s", site_url)

        email_input = await page.query_selector('input[type="email"], input[name*="email" i]')
        if not email_input:
            logger.warning("Could not find email input on this site")
            return False

        await email_input.fill(email)
        await page.wait_for_timeout(500)

        password_input = await page.query_selector('input[type="password"]')
        if not password_input:
            logger.warning("Could not find password input")
            return False

        await password_input.fill(password)
        submit_btn = await page.query_selector('button[type="submit"]')
        if submit_btn:
            await submit_btn.click()
            await page.wait_for_load_state("networkidle")
            logger.info("Login submitted")
            return True

        return False
    except Exception as exc:
        logger.error("Login failed: %s", exc)
        return False


async def navigate_to_product(page: Any, product_url: str) -> bool:
    try:
        await page.goto(product_url, wait_until="networkidle")
        logger.info("Product page loaded: %s", product_url)
        return True
    except Exception as exc:
        logger.error("Failed to navigate to product: %s", exc)
        return False


async def get_item_price(page: Any) -> float | None:
    try:
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
            element = await page.query_selector(selector)
            if element:
                price_text = await element.inner_text()
                break

        if not price_text:
            logger.warning("Could not find price on this page")
            return None

        price_match = re.search(r"\d+\.?\d*", price_text.replace(",", ""))
        if price_match:
            price = float(price_match.group())
            logger.info("Detected item price: $%s", price)
            return price

        logger.warning("Could not parse price from: %s", price_text)
        return None
    except Exception as exc:
        logger.error("Error getting price: %s", exc)
        return None


async def set_quantity(page: Any, quantity: int) -> int:
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
            element = await page.query_selector(selector)
            if element:
                tag = await element.evaluate("el => el.tagName.toLowerCase()")
                if tag == "select":
                    await element.select_option(str(quantity))
                else:
                    await element.triple_click()
                    await element.type(str(quantity))

                actual = await element.evaluate("el => el.value")
                try:
                    actual_qty = int(actual)
                except (ValueError, TypeError):
                    actual_qty = quantity

                if actual_qty < quantity:
                    logger.warning(
                        "Requested %s but site only allows %s; proceeding with accepted quantity",
                        quantity,
                        actual_qty,
                    )
                else:
                    logger.info("Quantity set to %s", actual_qty)
                return actual_qty

        logger.warning("Could not find quantity input; defaulting to 1")
        return 1
    except Exception as exc:
        logger.error("Failed to set quantity: %s", exc)
        return 1


async def add_to_cart(page: Any, *, dry_run: bool = False) -> bool:
    try:
        selectors = [
            'button:has-text("Add to Cart")',
            'button:has-text("Add to cart")',
            'button:has-text("Add to Basket")',
            'button[class*="add-to-cart" i]',
            '[class*="add-to-cart" i]',
        ]

        for selector in selectors:
            btn = await page.query_selector(selector)
            if btn:
                if dry_run:
                    logger.info("DRY RUN: Would click Add to Cart")
                    return True
                await btn.click()
                await page.wait_for_timeout(1500)
                await dismiss_mini_cart(page)
                logger.info("Item added to cart")
                return True

        logger.warning("Could not find Add to Cart button")
        return False
    except Exception as exc:
        logger.error("Failed to add to cart: %s", exc)
        return False


async def dismiss_mini_cart(page: Any) -> None:
    dismiss_selectors = [
        'button:has-text("Continue shopping")',
        'button:has-text("Continue Shopping")',
        'button:has-text("No thanks")',
        'button:has-text("No Thanks")',
        '[aria-label*="close" i]',
        '[class*="modal" i] [class*="close" i]',
    ]
    for selector in dismiss_selectors:
        button = await page.query_selector(selector)
        if button:
            await button.click()
            await page.wait_for_timeout(500)
            return


async def navigate_to_cart(page: Any) -> bool:
    try:
        cart_link_selectors = [
            'a:has-text("Go to Cart")',
            'a:has-text("View Cart")',
            'a:has-text("View cart")',
            'button:has-text("Go to Cart")',
            'button:has-text("View Cart")',
            '[class*="cart" i] a[href*="cart" i]',
        ]
        for selector in cart_link_selectors:
            link = await page.query_selector(selector)
            if link:
                await link.click()
                await page.wait_for_load_state("networkidle")
                logger.info("Navigated to cart via mini-cart link")
                return True

        parsed = urllib.parse.urlparse(page.url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        for path in ["/cart", "/basket", "/bag", "/checkout/cart"]:
            try:
                response = await page.goto(base + path, wait_until="networkidle")
                if response and response.ok:
                    logger.info("Navigated to cart via %s", base + path)
                    return True
            except Exception:
                continue

        logger.warning("Could not navigate to cart page")
        return False
    except Exception as exc:
        logger.error("Failed to navigate to cart: %s", exc)
        return False


async def select_shipping_address(page: Any, address: dict | None = None, *, dry_run: bool = False) -> bool:
    try:
        confirm_selectors = [
            'button:has-text("Deliver to this address")',
            'button:has-text("Use this address")',
            'button:has-text("Ship to this address")',
            'button:has-text("Deliver here")',
            '[class*="ship-to" i] button',
            '[class*="address" i] button[type="submit"]',
        ]
        for selector in confirm_selectors:
            button = await page.query_selector(selector)
            if button:
                if dry_run:
                    logger.info("DRY RUN: Would confirm default shipping address")
                    return True
                await button.click()
                await page.wait_for_load_state("networkidle")
                logger.info("Default shipping address confirmed")
                return True

        if address:
            filled = await fill_address_fields(page, address)
            if filled:
                logger.info("Filled %s address field(s) from stored address", filled)
                return True

        logger.info("No address picker found; assuming site default")
        return True
    except Exception as exc:
        logger.error("Error selecting shipping address: %s", exc)
        return False


async def fill_address_fields(page: Any, address: dict) -> int:
    field_map = [
        ('input[name*="fullName" i], input[name*="full_name" i], input[name*="name" i]', address.get("full_name", "")),
        ('input[name*="address1" i], input[name*="line1" i], input[id*="addressLine1" i]', address.get("line1", "")),
        ('input[name*="address2" i], input[name*="line2" i], input[id*="addressLine2" i]', address.get("line2", "")),
        ('input[name*="city" i], input[id*="city" i]', address.get("city", "")),
        ('input[name*="state" i], select[name*="state" i]', address.get("state", "")),
        ('input[name*="zip" i], input[name*="postal" i], input[id*="zipCode" i]', address.get("zip_code", "")),
    ]
    filled = 0
    for selector, value in field_map:
        if not value:
            continue
        element = await page.query_selector(selector)
        if not element:
            continue
        tag = await element.evaluate("el => el.tagName.toLowerCase()")
        if tag == "select":
            await element.select_option(value)
        else:
            await element.triple_click()
            await element.type(value)
        filled += 1
    return filled


async def checkout(page: Any, *, dry_run: bool = False) -> bool:
    try:
        selectors = [
            'button:has-text("Checkout")',
            'button:has-text("Proceed to Checkout")',
            'a:has-text("Checkout")',
            '[class*="checkout" i]',
        ]
        for selector in selectors:
            button = await page.query_selector(selector)
            if button:
                if dry_run:
                    logger.info("DRY RUN: Would proceed to checkout")
                    return True
                await button.click()
                await page.wait_for_load_state("networkidle")
                logger.info("Proceeded to checkout")
                return True

        logger.warning("Could not find checkout button")
        return False
    except Exception as exc:
        logger.error("Checkout failed: %s", exc)
        return False


async def complete_purchase(page: Any, *, dry_run: bool = False, review_mode: bool = False) -> bool:
    try:
        selectors = [
            'button:has-text("Place Order")',
            'button:has-text("Complete Purchase")',
            'button:has-text("Confirm Order")',
            'button:has-text("Buy Now")',
        ]
        for selector in selectors:
            button = await page.query_selector(selector)
            if button:
                if dry_run:
                    logger.info("DRY RUN: Would complete purchase")
                    return True
                if review_mode:
                    logger.info("REVIEW MODE: Final purchase button found; stopping for approval")
                    return True
                await button.click()
                await page.wait_for_load_state("networkidle")
                logger.info("Purchase completed")
                return True

        logger.warning("Could not find purchase confirmation button")
        return False
    except Exception as exc:
        logger.error("Failed to complete purchase: %s", exc)
        return False
