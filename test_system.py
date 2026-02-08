#!/usr/bin/env python3
"""
AutoNation Appraisal System - Complete Test Suite

Run this script after installing dependencies to verify everything works.

Usage:
    python3 test_system.py
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_mock_market_data():
    """Test mock market data loading."""
    print_header("TEST 1: Mock Market Data")

    try:
        from tools.api_mocks import get_market_intelligence

        vin = "1HGBH41JXMN109186"
        result = get_market_intelligence(vin, "33130")

        if result.get("success"):
            print(f"✅ PASS")
            print(f"   Vehicle: {result['vehicle_info']['year']} {result['vehicle_info']['make']} {result['vehicle_info']['model']}")
            print(f"   KBB Offer: ${result['kbb_valuation']['instant_cash_offer']:,}")
            print(f"   Market Avg: ${result['market_summary']['avg_price']:,}")
            print(f"   Comparables: {len(result['comparables'])}")
            return True
        else:
            print(f"❌ FAIL: {result.get('error')}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_nhtsa_api():
    """Test NHTSA VIN decoder (requires 'requests' package)."""
    print_header("TEST 2: NHTSA VIN Decoder (Real API)")

    try:
        from tools.nhtsa_api import decode_vin

        vin = "1HGBH41JXMN109186"
        print(f"   Decoding VIN: {vin}")
        print(f"   Calling NHTSA API...")

        result = decode_vin(vin)

        if result.get("success"):
            print(f"✅ PASS")
            print(f"   Make: {result.get('make', 'N/A')}")
            print(f"   Model: {result.get('model', 'N/A')}")
            print(f"   Year: {result.get('year', 'N/A')}")
            return True
        else:
            print(f"❌ FAIL: {result.get('error')}")
            return False
    except ImportError as e:
        print(f"⚠️  SKIP: Missing dependency - {e}")
        print(f"   Install with: pip install requests")
        return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_reconditioning_cost():
    """Test reconditioning cost estimation."""
    print_header("TEST 3: Reconditioning Cost Calculator")

    try:
        from agents.vision_analyst import estimate_reconditioning_cost

        issues = ["scratches_bumper", "seat_wear", "aftermarket_wheels"]
        result = estimate_reconditioning_cost(issues)

        if result.get("status") == "success":
            print(f"✅ PASS")
            print(f"   Recon Cost: ${result['total_reconditioning_cost']:,}")
            print(f"   Aftermarket Value: +${result['aftermarket_value_added']:,}")
            print(f"   Net Adjustment: ${result['net_adjustment']:+,}")
            return True
        else:
            print(f"❌ FAIL")
            return False
    except ImportError as e:
        print(f"⚠️  SKIP: Missing ADK - {e}")
        print(f"   Install with: pip install google-adk")
        return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_pricing_scenarios():
    """Test pricing scenario calculations."""
    print_header("TEST 4: Pricing Scenario Calculator")

    try:
        from agents.pricing_strategist import calculate_offer_scenarios

        result = calculate_offer_scenarios(
            market_avg_price=24980,
            kbb_instant_offer=23800,
            recon_cost=700,
            aftermarket_value=800
        )

        if result.get("status") == "success":
            balanced = result["scenarios"]["balanced"]
            print(f"✅ PASS")
            print(f"   Recommended Offer: ${balanced['offer_price']:,.2f}")
            print(f"   Win Rate: {balanced['win_rate_estimate']*100:.0f}%")
            print(f"   Expected Profit: ${balanced['expected_profit']:,.2f}")
            return True
        else:
            print(f"❌ FAIL")
            return False
    except ImportError as e:
        print(f"⚠️  SKIP: Missing ADK - {e}")
        print(f"   Install with: pip install google-adk")
        return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_full_workflow():
    """Test complete end-to-end workflow."""
    print_header("TEST 5: Complete Workflow Integration")

    try:
        from tools.api_mocks import get_market_intelligence
        from agents.vision_analyst import estimate_reconditioning_cost
        from agents.pricing_strategist import calculate_offer_scenarios

        # Step 1: Market intelligence
        vin = "1HGBH41JXMN109186"
        market_data = get_market_intelligence(vin)
        if not market_data.get("success"):
            print("❌ FAIL: Market intelligence failed")
            return False

        # Step 2: Condition analysis
        issues = ["scratches_bumper", "aftermarket_wheels"]
        recon_data = estimate_reconditioning_cost(issues)
        if recon_data.get("status") != "success":
            print("❌ FAIL: Recon estimation failed")
            return False

        # Step 3: Pricing recommendation
        scenarios = calculate_offer_scenarios(
            market_data["market_summary"]["avg_price"],
            market_data["kbb_valuation"]["instant_cash_offer"],
            recon_data["total_reconditioning_cost"],
            recon_data["aftermarket_value_added"]
        )

        if scenarios.get("status") == "success":
            offer = scenarios["scenarios"]["balanced"]["offer_price"]
            print(f"✅ PASS")
            print(f"\n   FINAL RECOMMENDATION:")
            print(f"   Vehicle: 2022 Honda Accord")
            print(f"   Market Avg: ${market_data['market_summary']['avg_price']:,}")
            print(f"   Recommended Offer: ${offer:,.2f}")
            print(f"   Win Probability: {scenarios['scenarios']['balanced']['win_rate_estimate']*100:.0f}%")
            return True
        else:
            print("❌ FAIL: Pricing failed")
            return False

    except ImportError as e:
        print(f"⚠️  SKIP: Missing dependencies - {e}")
        return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "🚗 "*35)
    print("  AutoNation Intelligent Appraisal System - Test Suite")
    print("🚗 "*35)

    tests = [
        ("Mock Market Data", test_mock_market_data),
        ("NHTSA API", test_nhtsa_api),
        ("Reconditioning Cost", test_reconditioning_cost),
        ("Pricing Scenarios", test_pricing_scenarios),
        ("Full Workflow", test_full_workflow),
    ]

    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))

    # Summary
    print_header("TEST SUMMARY")

    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    skipped = sum(1 for _, r in results if r is None)

    for name, result in results:
        status = "✅ PASS" if result is True else "❌ FAIL" if result is False else "⚠️  SKIP"
        print(f"   {status}  {name}")

    print(f"\n   Total: {len(results)} tests")
    print(f"   Passed: {passed} | Failed: {failed} | Skipped: {skipped}")

    if failed > 0:
        print(f"\n   ❌ Some tests failed. Check errors above.")
        sys.exit(1)
    elif skipped > 0:
        print(f"\n   ⚠️  Some tests skipped due to missing dependencies.")
        print(f"   Install missing packages:")
        print(f"     pip install requests google-adk streamlit pandas plotly")
        sys.exit(0)
    else:
        print(f"\n   ✅ All tests passed! System is ready.")
        sys.exit(0)


if __name__ == "__main__":
    main()
