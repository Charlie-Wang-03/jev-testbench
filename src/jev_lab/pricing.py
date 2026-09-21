"""Central price table for TypeSafe models.

Local cost estimates are derived from the *resolved* model reported by the API, never from the
model we asked for: an alias such as ``jev-latest`` may point somewhere else tomorrow, and a
price change must not silently change what we record.

An unknown model yields ``None`` (recorded as ``cost_basis="unknown"``) rather than a guess.
Console billing remains the authoritative server-side record; these numbers are local estimates.
"""

from dataclasses import dataclass

from typesafe_sdk import SystemOneResponse, Usage

MILLION = 1_000_000


@dataclass(frozen=True)
class ModelPrice:
    """Published USD price per one million tokens for a single model."""

    input_usd_per_million: float
    output_usd_per_million: float

    def usd(self, input_tokens: int | None, output_tokens: int | None) -> float:
        """Estimated USD for the given token counts."""
        return (
            (input_tokens or 0) * self.input_usd_per_million / MILLION
            + (output_tokens or 0) * self.output_usd_per_million / MILLION
        )

    def basis(self, model: str) -> str:
        """A human-readable, loggable description of how a cost was derived."""
        return (
            f"{model}: input ${self.input_usd_per_million}/M tokens, "
            f"output ${self.output_usd_per_million}/M tokens"
        )


# Official published prices for jev-1.13.0: $0.042 / 1M input tokens, output free.
# Source: https://docs.typesafe.ai/models
PRICES: dict[str, ModelPrice] = {
    "jev-1.13.0": ModelPrice(input_usd_per_million=0.042, output_usd_per_million=0.0),
}

UNKNOWN_COST_BASIS = "unknown: resolved model is not in this project's price table"


def price_for(model: str | None) -> ModelPrice | None:
    """Look up the price for an exact model name, or ``None`` if it is not in the table."""
    if not model:
        return None
    return PRICES.get(model)


def estimate_cost(response: SystemOneResponse) -> tuple[float | None, str]:
    """Return ``(estimated_usd, cost_basis)`` for a response, keyed on its resolved model.

    Returns ``(None, UNKNOWN_COST_BASIS)`` when the resolved model has no known price, so that a
    new or renamed model can never be billed against the wrong rate.
    """
    resolved = getattr(response, "model", None)
    price = price_for(resolved)
    if price is None:
        return None, UNKNOWN_COST_BASIS
    usage = response.usage
    return price.usd(usage.input_tokens, usage.output_tokens), price.basis(resolved)


def token_counts(usage: Usage | None) -> tuple[int, int, int]:
    """Return ``(input_tokens, output_tokens, total_tokens)``, treating unreported counts as zero."""
    if usage is None:
        return 0, 0, 0
    input_tokens = usage.input_tokens or 0
    output_tokens = usage.output_tokens or 0
    return input_tokens, output_tokens, input_tokens + output_tokens
