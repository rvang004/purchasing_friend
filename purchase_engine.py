"""Purchase automation engine using Playwright.

The engine now orchestrates the flow while `purchase_actions` owns generic
selectors. Next stop someday: real site adapters. For now, less goblin soup.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from purchase_adapters import StoreAdapter, select_adapter
from purchase_artifacts import PurchaseArtifacts

logger = logging.getLogger(__name__)

VALID_MODES = {"dry-run", "review", "live"}


class PurchaseEngine:
    """Automated purchase executor."""

    def __init__(
        self,
        headless: bool = True,
        dry_run: bool = False,
        mode: str | None = None,
        artifacts: PurchaseArtifacts | None = None,
        adapter: StoreAdapter | None = None,
    ):
        self.headless = headless
        self.mode = self._resolve_mode(mode, dry_run)
        self.dry_run = self.mode == "dry-run"
        self.review_mode = self.mode == "review"
        self.playwright: Any = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.artifacts = artifacts or PurchaseArtifacts()
        self.adapter = adapter
        self.trace_path: str | None = None

    async def initialize(self) -> None:
        """Start browser instance and trace capture."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        await self.artifacts.start_trace(self.context)
        self.page = await self.context.new_page()
        logger.info("Browser initialized in %s mode", self.mode)

    async def close(self) -> None:
        """Close browser and persist trace if available."""
        if self.context:
            self.trace_path = await self.artifacts.stop_trace(self.context)
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed")

    async def execute_purchase(self, account: dict[str, Any], product_url: str, quantity: int = 1) -> dict[str, Any]:
        """Execute full purchase flow."""
        result = {
            "success": False,
            "account_id": account.get("id"),
            "product_url": product_url,
            "timestamp": datetime.now().isoformat(),
            "error": None,
            "item_price": None,
            "quantity": quantity,
            "mode": self.mode,
            "review_required": self.review_mode,
            "artifact_dir": str(self.artifacts.run_dir),
            "screenshots": [],
            "trace_path": None,
        }

        try:
            self.adapter = self.adapter or select_adapter(account, product_url)
            result["adapter"] = self.adapter.name

            if not await self._login(account, result):
                return result
            if not await self._load_product(product_url, result):
                return result

            actual_quantity = await self.adapter.set_quantity(self.page, quantity)
            result["quantity"] = actual_quantity
            await self._screenshot("03_quantity", result)

            item_price = await self.adapter.get_item_price(self.page)
            result["item_price"] = item_price
            if self._price_blocked(account, item_price, result):
                return result

            if not await self.adapter.add_to_cart(self.page, dry_run=self.dry_run):
                result["error"] = "Failed to add to cart"
                return result
            await self._screenshot("04_cart_added", result)

            if not await self.adapter.navigate_to_cart(self.page):
                result["error"] = "Failed to reach cart page"
                return result
            await self._screenshot("05_cart", result)

            if not await self.adapter.checkout(self.page, dry_run=self.dry_run):
                result["error"] = "Checkout failed"
                return result
            await self._screenshot("06_checkout", result)

            await self.adapter.select_shipping_address(
                self.page,
                account.get("shipping_address"),
                dry_run=self.dry_run,
            )
            await self._screenshot("07_shipping", result)

            if not await self.adapter.complete_purchase(
                self.page,
                dry_run=self.dry_run,
                review_mode=self.review_mode,
            ):
                result["error"] = "Failed to complete purchase"
                return result
            await self._screenshot("08_final", result)
            result["final_url"] = self.page.url

            result["success"] = True
            if self.review_mode:
                result["message"] = "Review required before final purchase click"
            logger.info(
                "Purchase flow successful for %s; qty=%s price=%s mode=%s",
                account.get("id"),
                actual_quantity,
                item_price,
                self.mode,
            )
        except Exception as exc:
            result["error"] = str(exc)
            logger.error("Unexpected purchase error: %s", exc)

        return result

    async def _login(self, account: dict[str, Any], result: dict[str, Any]) -> bool:
        if await self.adapter.login(self.page, account):
            await self._screenshot("01_login", result)
            return True
        result["error"] = "Login failed"
        await self._screenshot("01_login_failed", result)
        return False

    async def _load_product(self, product_url: str, result: dict[str, Any]) -> bool:
        if await self.adapter.navigate_to_product(self.page, product_url):
            await self._screenshot("02_product", result)
            return True
        result["error"] = "Failed to navigate to product"
        return False

    def _price_blocked(self, account: dict[str, Any], item_price: float | None, result: dict[str, Any]) -> bool:
        price_limit_enabled = account.get("price_limit_enabled", True)
        price_limit = account.get("price_limit_per_item")

        if price_limit_enabled and price_limit and item_price:
            if item_price > price_limit:
                result["error"] = f"Item price (${item_price}) exceeds limit (${price_limit})"
                logger.warning(result["error"])
                return True
        elif item_price is None and price_limit_enabled and self.mode == "live":
            result["error"] = "Could not verify price in live mode"
            logger.warning(result["error"])
            return True
        elif item_price is None and price_limit_enabled:
            logger.warning("Could not detect price; non-live mode may continue")
        elif not price_limit_enabled:
            logger.info("Price limit disabled for this account")

        return False

    async def _screenshot(self, name: str, result: dict[str, Any]) -> None:
        path = await self.artifacts.screenshot(self.page, name)
        if path:
            result["screenshots"].append(path)

    @staticmethod
    def _resolve_mode(mode: str | None, dry_run: bool) -> str:
        resolved = mode or ("dry-run" if dry_run else "live")
        if resolved not in VALID_MODES:
            raise ValueError(f"mode must be one of {sorted(VALID_MODES)}")
        return resolved


async def run_purchase(
    account: dict[str, Any],
    product_url: str,
    quantity: int = 1,
    dry_run: bool = False,
    mode: str | None = None,
) -> dict[str, Any]:
    """Standalone function to execute a single purchase."""
    run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{account.get('id', 'account')}"
    engine = PurchaseEngine(
        headless=True,
        dry_run=dry_run,
        mode=mode,
        artifacts=PurchaseArtifacts(run_id=run_id),
    )

    result: dict[str, Any] | None = None
    try:
        await engine.initialize()
        result = await engine.execute_purchase(account, product_url, quantity=quantity)
    finally:
        await engine.close()
        if result is not None:
            result["trace_path"] = engine.trace_path

    return result
