"""Cost estimation and price-table behaviour. Offline: constructs responses, never calls the API."""

from typesafe_sdk import SystemOneResponse, Usage

from jev_lab.pricing import (
    MILLION,
    PRICES,
    UNKNOWN_COST_BASIS,
    ModelPrice,
    estimate_cost,
    price_for,
    token_counts,
)


def make_response(model: str, input_tokens: int, output_tokens: int) -> SystemOneResponse:
    """A minimal response carrying only the fields cost estimation reads."""
    return SystemOneResponse(
        model=model,
        usage=Usage(input_tokens=input_tokens, output_tokens=output_tokens),
        answers={},
    )


class TestPriceTable:
    def test_jev_1_13_input_price_matches_published_rate(self):
        assert PRICES["jev-1.13.0"].input_usd_per_million == 0.042

    def test_output_tokens_are_free_for_jev_1_13(self):
        assert PRICES["jev-1.13.0"].output_usd_per_million == 0.0

    def test_unknown_model_has_no_price(self):
        assert price_for("jev-9.9.9") is None

    def test_missing_model_name_has_no_price(self):
        assert price_for(None) is None


class TestCostArithmetic:
    def test_one_million_input_tokens_costs_the_headline_rate(self):
        price = ModelPrice(input_usd_per_million=0.042, output_usd_per_million=0.0)
        assert price.usd(MILLION, 0) == 0.042

    def test_cost_scales_linearly_with_input_tokens(self):
        price = ModelPrice(input_usd_per_million=0.042, output_usd_per_million=0.0)
        # 1000 input tokens at $0.042/1M = $0.000042
        assert round(price.usd(1000, 0), 10) == 0.000042

    def test_output_tokens_do_not_add_cost_when_free(self):
        price = ModelPrice(input_usd_per_million=0.042, output_usd_per_million=0.0)
        assert price.usd(1000, 999_999) == price.usd(1000, 0)

    def test_paid_output_tokens_are_added(self):
        price = ModelPrice(input_usd_per_million=1.0, output_usd_per_million=2.0)
        assert price.usd(MILLION, MILLION) == 3.0

    def test_none_token_counts_are_treated_as_zero(self):
        price = ModelPrice(input_usd_per_million=0.042, output_usd_per_million=0.0)
        assert price.usd(None, None) == 0.0

    def test_basis_names_the_model_and_the_rates(self):
        basis = PRICES["jev-1.13.0"].basis("jev-1.13.0")
        assert "jev-1.13.0" in basis and "0.042" in basis


class TestEstimateCost:
    def test_estimate_uses_the_resolved_model(self):
        cost, basis = estimate_cost(make_response("jev-1.13.0", input_tokens=1000, output_tokens=500))
        assert round(cost, 10) == 0.000042
        assert "jev-1.13.0" in basis

    def test_unknown_resolved_model_reports_unknown_rather_than_guessing(self):
        cost, basis = estimate_cost(make_response("jev-future", input_tokens=1000, output_tokens=500))
        assert cost is None
        assert basis == UNKNOWN_COST_BASIS


class TestTokenCounts:
    def test_total_is_input_plus_output(self):
        assert token_counts(Usage(input_tokens=120, output_tokens=12)) == (120, 12, 132)

    def test_unreported_usage_becomes_zero(self):
        assert token_counts(None) == (0, 0, 0)

    def test_unreported_counts_are_treated_as_zero(self):
        assert token_counts(Usage(input_tokens=None, output_tokens=None)) == (0, 0, 0)
