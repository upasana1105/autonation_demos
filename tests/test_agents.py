"""
Unit tests for AutoNation appraisal agents and tools.
"""

import sys
import os
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.nhtsa_api import decode_vin, validate_vin
from tools.api_mocks import get_kbb_instant_cash_offer, get_cargurus_comparables, get_market_intelligence
from agents.vision_analyst import estimate_reconditioning_cost
from agents.pricing_strategist import calculate_offer_scenarios, calculate_competitive_position


class TestNHTSAAPI:
    """Test NHTSA VIN decoder (real API)."""

    def test_decode_valid_vin(self):
        """Test decoding a valid VIN."""
        # Using a known valid VIN from demo data
        vin = "1HGBH41JXMN109186"
        result = decode_vin(vin)

        assert result["success"] == True
        assert result["vin"] == vin
        assert "make" in result
        assert "model" in result
        assert "year" in result

    def test_decode_invalid_vin(self):
        """Test decoding an invalid VIN."""
        vin = "INVALID"
        result = decode_vin(vin)

        assert result["success"] == False
        assert "error" in result

    def test_validate_vin(self):
        """Test VIN validation."""
        vin = "1HGBH41JXMN109186"
        result = validate_vin(vin)

        assert result.get("valid") == True or result.get("success") == True


class TestMockAPIs:
    """Test mock API functions."""

    def test_kbb_instant_offer(self):
        """Test KBB instant cash offer mock."""
        vin = "1HGBH41JXMN109186"
        result = get_kbb_instant_cash_offer(vin)

        assert result["success"] == True
        assert "data" in result
        assert "instant_cash_offer" in result["data"]
        assert result["data"]["instant_cash_offer"] > 0

    def test_cargurus_comparables(self):
        """Test CarGurus comparables mock."""
        vin = "1HGBH41JXMN109186"
        result = get_cargurus_comparables(vin)

        assert result["success"] == True
        assert "comparables" in result
        assert len(result["comparables"]) > 0
        assert "market_summary" in result

    def test_market_intelligence(self):
        """Test combined market intelligence."""
        vin = "1HGBH41JXMN109186"
        result = get_market_intelligence(vin)

        assert result["success"] == True
        assert "vehicle_info" in result
        assert "kbb_valuation" in result
        assert "comparables" in result
        assert "market_summary" in result

    def test_unknown_vin(self):
        """Test handling of unknown VIN."""
        vin = "UNKNOWN12345678901"
        result = get_market_intelligence(vin)

        assert result["success"] == False


class TestVisionAnalystTools:
    """Test vision analyst tools."""

    def test_estimate_recon_cost_basic(self):
        """Test basic reconditioning cost estimation."""
        issues = ["scratches_bumper", "seat_wear"]
        result = estimate_reconditioning_cost(issues)

        assert result["status"] == "success"
        assert "total_reconditioning_cost" in result
        assert result["total_reconditioning_cost"] > 0
        assert "breakdown" in result

    def test_estimate_recon_cost_aftermarket(self):
        """Test with aftermarket modifications."""
        issues = ["scratches_bumper", "aftermarket_wheels"]
        result = estimate_reconditioning_cost(issues)

        assert result["status"] == "success"
        assert "aftermarket_value_added" in result
        assert result["aftermarket_value_added"] > 0
        assert "net_adjustment" in result

    def test_estimate_recon_cost_empty(self):
        """Test with no issues."""
        issues = []
        result = estimate_reconditioning_cost(issues)

        assert result["status"] == "success"
        assert result["total_reconditioning_cost"] == 0


class TestPricingStrategistTools:
    """Test pricing strategist tools."""

    def test_calculate_offer_scenarios(self):
        """Test offer scenario calculation."""
        market_avg = 25000
        kbb_offer = 23800
        recon_cost = 400
        aftermarket_value = 800

        result = calculate_offer_scenarios(
            market_avg, kbb_offer, recon_cost, aftermarket_value
        )

        assert result["status"] == "success"
        assert "scenarios" in result
        assert "aggressive" in result["scenarios"]
        assert "balanced" in result["scenarios"]
        assert "conservative" in result["scenarios"]

        # Balanced offer should be between aggressive and conservative
        agg_offer = result["scenarios"]["aggressive"]["offer_price"]
        bal_offer = result["scenarios"]["balanced"]["offer_price"]
        con_offer = result["scenarios"]["conservative"]["offer_price"]

        assert agg_offer < bal_offer < con_offer

    def test_calculate_competitive_position(self):
        """Test competitive position analysis."""
        our_offer = 24500
        kbb_offer = 23800
        market_avg = 25000

        result = calculate_competitive_position(
            our_offer, kbb_offer, market_avg
        )

        assert result["status"] == "success"
        assert "competitive_position" in result
        assert "vs_kbb" in result
        assert "vs_market_avg" in result

        # Our offer is above KBB, so should be competitive
        assert result["vs_kbb"]["difference"] > 0

    def test_competitive_position_below_kbb(self):
        """Test position when offer is below KBB."""
        our_offer = 23000
        kbb_offer = 24000
        market_avg = 25000

        result = calculate_competitive_position(
            our_offer, kbb_offer, market_avg
        )

        assert result["competitive_position"] in ["Below Market", "Market Rate"]


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_full_appraisal_flow(self):
        """Test complete appraisal flow."""
        vin = "1HGBH41JXMN109186"

        # Step 1: Get market intelligence
        market_data = get_market_intelligence(vin)
        assert market_data["success"] == True

        # Step 2: Estimate recon costs
        issues = ["scratches_bumper", "aftermarket_wheels"]
        recon_data = estimate_reconditioning_cost(issues)
        assert recon_data["status"] == "success"

        # Step 3: Calculate offer scenarios
        scenarios = calculate_offer_scenarios(
            market_data["market_summary"]["avg_price"],
            market_data["kbb_valuation"]["instant_cash_offer"],
            recon_data["total_reconditioning_cost"],
            recon_data["aftermarket_value_added"]
        )
        assert scenarios["status"] == "success"

        # Verify recommended offer is reasonable
        recommended_offer = scenarios["scenarios"]["balanced"]["offer_price"]
        assert 20000 < recommended_offer < 30000


# Run tests with: pytest tests/test_agents.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
