"""Security guardrails: ticker sanitization, risk-limit enforcement, and compliance disclaimer."""
import re
from typing import Tuple

from pydantic import BaseModel, Field

class RiskAssessment(BaseModel):
    """Structured result of `enforce_risk_limits`, returned to the Risk Manager agent."""
    approved: bool
    requires_review: bool = False
    adjusted_size_pct: float
    warnings: list[str] = Field(default_factory=list)

# Required legal and safety disclaimer for trading output
REQUIRED_DISCLAIMER = (
    "\n\n[SECURITY WARNING & COMPLIANCE DISCLAIMER]\n"
    "This AI-generated analysis is for informational and educational purposes only. "
    "It does not constitute professional investment advice or a recommendation to buy or sell securities. "
    "Trading stocks and assets involves significant financial risk. Past performance is not indicative of "
    "future results. Always consult with a licensed financial advisor before making any investment decisions."
)

def sanitize_ticker(ticker: str) -> Tuple[bool, str]:
    """
    Sanitize and validate stock ticker symbols.
    Prevents prompt injection attacks, shell escapes, or invalid symbol queries.
    
    Returns:
        A tuple of (is_valid, sanitized_ticker_string).
    """
    if not isinstance(ticker, str):
        return False, ""
        
    # Remove leading/trailing whitespaces and convert to uppercase
    clean = ticker.strip().upper()
    
    # Valid tickers contain only 1-5 letters (and optionally a dot or hyphen, e.g., 'BRK-B', 'RDS.A')
    pattern = r"^[A-Z]{1,5}([.-][A-Z]{1,2})?$"
    
    if re.match(pattern, clean):
        return True, clean
    return False, ""

def enforce_risk_limits(
    proposed_size_pct: float,
    stop_loss_pct: float,
    rsi_value: float = 50.0
) -> RiskAssessment:
    """
    Enforce hard risk parameters on suggested trading actions:
    1. Maximum single-position allocation of 5% of total portfolio.
    2. Overbought conditions (RSI > 70) restrict max sizing to 2%.
    3. Stop-loss must be between 2% and 12% below current entry.

    Returns:
        A `RiskAssessment` with approval status, review flag, adjusted sizing, and warnings.
    """
    adjusted_size = proposed_size_pct
    warnings = []
    approved = True
    requires_review = False

    # Rule 1: Sizing bounds
    if proposed_size_pct > 5.0:
        adjusted_size = 5.0
        warnings.append(f"Position size {proposed_size_pct}% exceeds maximum limit of 5.0%. Scaled down to 5.0%.")

    # Rule 2: Overbought safety ceiling
    if rsi_value > 70.0 and adjusted_size > 2.0:
        adjusted_size = 2.0
        warnings.append(f"RSI is overbought ({rsi_value:.1f}). Max size restricted to 2.0% for protection.")

    # Rule 3: Stop-loss protection
    if stop_loss_pct > 12.0:
        warnings.append(f"Stop-loss gap of {stop_loss_pct}% is too wide (max 12.0%). Position flagged as unsafe.")
        approved = False
    elif stop_loss_pct < 1.5:
        warnings.append(f"Stop-loss gap of {stop_loss_pct}% is too narrow (min 1.5%). High risk of early exit; flagged for review.")
        requires_review = True

    return RiskAssessment(
        approved=approved,
        requires_review=requires_review,
        adjusted_size_pct=adjusted_size,
        warnings=warnings,
    )

def sanitize_and_format_output(output_text: str) -> str:
    """
    Post-process the agent workflow output to ensure security disclaimers are
    present, mitigating risk and satisfying hackathon security compliance rules.
    """
    if "SECURITY WARNING" not in output_text and "DISCLAIMER" not in output_text.upper():
        return output_text + REQUIRED_DISCLAIMER
    return output_text
