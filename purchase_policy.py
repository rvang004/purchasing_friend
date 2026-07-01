"""Safety policy checks for purchase execution.

This module owns the "should we allow this?" decisions. The browser engine
should click buttons; policy should decide whether buttons are allowed. SOLID,
not soup. Delicious soup, bad architecture.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from models import Account, PurchaseResult, PurchaseTask


@dataclass(frozen=True)
class PolicyDecision:
    """Result of a safety policy check."""

    allowed: bool
    reason: str = "allowed"

    @classmethod
    def allow(cls) -> "PolicyDecision":
        return cls(True, "allowed")

    @classmethod
    def block(cls, reason: str) -> "PolicyDecision":
        return cls(False, reason)


def validate_task_for_account(task: PurchaseTask, account: Account | None) -> PolicyDecision:
    """Validate a task before any browser automation starts."""
    if account is None:
        return PolicyDecision.block("Account not found")

    if not task.enabled:
        return PolicyDecision.block("Task is disabled")

    if task.quantity < 1:
        return PolicyDecision.block("Quantity must be at least 1")

    if account.quantity_limit_per_item is not None:
        if task.quantity > account.quantity_limit_per_item:
            return PolicyDecision.block(
                f"Quantity {task.quantity} exceeds limit {account.quantity_limit_per_item}"
            )

    if account.spent_this_month >= account.monthly_limit:
        return PolicyDecision.block("Monthly limit reached")

    return PolicyDecision.allow()


def validate_purchase_result(account: Account, result: PurchaseResult) -> PolicyDecision:
    """Validate the engine result before recording a successful live purchase."""
    if not result.success:
        return PolicyDecision.block(result.error or "Purchase failed")

    if result.dry_run:
        return PolicyDecision.allow()

    if account.price_limit_enabled and account.price_limit_per_item is not None:
        if result.item_price is None:
            return PolicyDecision.block("Price could not be verified")
        if result.item_price > account.price_limit_per_item:
            return PolicyDecision.block(
                f"Item price {result.item_price} exceeds limit {account.price_limit_per_item}"
            )

    projected_spend = account.spent_this_month + spend_amount(result)
    if projected_spend > account.monthly_limit:
        return PolicyDecision.block(
            f"Purchase would exceed monthly limit ({projected_spend} > {account.monthly_limit})"
        )

    return PolicyDecision.allow()


def spend_amount(result: PurchaseResult) -> Decimal:
    """Amount to add to monthly spend for a successful live purchase."""
    if not result.success or result.dry_run:
        return Decimal("0.00")
    if result.order_total is not None:
        return result.order_total
    if result.item_price is not None:
        return (result.item_price * Decimal(result.quantity)).quantize(Decimal("0.01"))
    return Decimal("0.00")
