from django import template
from core.constants import CURRENCY_SYMBOL

register = template.Library()

@register.filter
def rupees(value):
    """Format number as rupees with proper comma separation"""
    try:
        if value is None:
            return f"{CURRENCY_SYMBOL}0.00"
        # Format with commas for thousands separator and 2 decimal places
        return f"{CURRENCY_SYMBOL}{value:,.2f}"
    except (ValueError, TypeError):
        return f"{CURRENCY_SYMBOL}0.00"

@register.filter
def rupees_int(value):
    """Format number as rupees without decimals"""
    try:
        if value is None:
            return f"{CURRENCY_SYMBOL}0"
        return f"{CURRENCY_SYMBOL}{value:,.0f}"
    except (ValueError, TypeError):
        return f"{CURRENCY_SYMBOL}0"

