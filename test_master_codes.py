#!/usr/bin/env python3
"""
Test NextGen API Master/Codes endpoint using the real implementation.
Run this from the root directory of your project.

Usage:
    python3 test_master_codes.py
"""

import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

try:
    from nextgen_api.client.nextgen_client import NextGenClient
    from nextgen_api.exceptions.nextgen_exceptions import NextGenAPIError

    def test_real_implementation():
        print("🔧 Testing NextGen API with Real Implementation...")
        print("=" * 60)

        # Step 1: Initialize client
        try:
            print("🚀 Initializing NextGen client...")
            client = NextGenClient()

            print(f"✅ Client initialized successfully")
            print(f"   {client}")
            print(f"   Client info: {client.get_client_info()}")
            print()

        except Exception as e:
            print(f"❌ Failed to initialize client: {e}")
            return False

        # Step 2: Test connection
        try:
            print("🔗 Testing API connection...")
            if client.test_connection():
                print("✅ Connection test passed!")
            else:
                print("❌ Connection test failed!")
                return False
            print()

        except Exception as e:
            print(f"❌ Connection test error: {e}")
            return False

        # Step 3: Get master codes using real service
        try:
            print("📋 Fetching master codes...")
            codes_response = client.master.get_codes()

            print(f"✅ Master codes retrieved successfully!")
            print(f"   Total categories: {codes_response.total_count}")
            print(f"   Response type: {type(codes_response)}")
            print()

            # Show first few codes
            print("   First 10 code categories:")
            for i, code in enumerate(codes_response.codes[:10]):
                print(f"      {i+1:2d}. {code}")

            if codes_response.total_count > 10:
                print(f"      ... and {codes_response.total_count - 10} more")
            print()

        except Exception as e:
            print(f"❌ Failed to fetch master codes: {e}")
            return False

        # Step 4: Test filtering functionality
        try:
            print("🔍 Testing code filtering...")

            # Test pattern matching
            patterns_to_test = ["appointment", "condition", "diagnosis", "allerg"]

            for pattern in patterns_to_test:
                matching_codes = codes_response.get_codes_by_pattern(pattern)
                print(f"   '{pattern}' pattern: {len(matching_codes)} matches")
                if matching_codes:
                    print(f"      Examples: {matching_codes[:3]}")
            print()

        except Exception as e:
            print(f"❌ Failed to test filtering: {e}")
            return False

        # Step 5: Test specific code checking
        try:
            print("✅ Testing code existence checks...")

            test_codes = [
                "2012_condition_codes",
                "appointment_status_codes",
                "nonexistent_code_category"
            ]

            for code in test_codes:
                exists = codes_response.has_code(code)
                status = "✅ EXISTS" if exists else "❌ NOT FOUND"
                print(f"   {code}: {status}")
            print()

        except Exception as e:
            print(f"❌ Failed to test code checks: {e}")
            return False

        # Step 6: Save response for analysis
        try:
            print("💾 Saving response data...")

            # Save full response as JSON
            output_data = {
                "total_count": codes_response.total_count,
                "codes": codes_response.codes,
                "timestamp": str(Path(__file__).stat().st_mtime),
                "client_info": client.get_client_info()
            }

            output_file = project_root / "master_codes_response.json"
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)

            print(f"   ✅ Response saved to: {output_file}")
            print(f"   📊 File size: {output_file.stat().st_size} bytes")
            print()

        except Exception as e:
            print(f"❌ Failed to save response: {e}")
            # Don't return False - this isn't critical

        # Step 7: Pattern analysis
        try:
            print("📊 Analyzing code patterns...")

            patterns = {}
            for code in codes_response.codes:
                # Extract base pattern (before first underscore or dash)
                if '_' in code:
                    base = code.split('_')[0]
                elif '-' in code:
                    base = code.split('-')[0]
                else:
                    base = code

                if base not in patterns:
                    patterns[base] = []
                patterns[base].append(code)

            print(f"   Found {len(patterns)} base patterns:")

            # Show top patterns
            sorted_patterns = sorted(patterns.items(), key=lambda x: len(x[1]), reverse=True)
            for pattern, codes in sorted_patterns[:10]:
                if len(codes) <= 3:
                    print(f"      {pattern} ({len(codes)}): {codes}")
                else:
                    print(f"      {pattern} ({len(codes)}): {codes[:2]}...+{len(codes)-2} more")

            if len(sorted_patterns) > 10:
                print(f"      ... and {len(sorted_patterns) - 10} more patterns")
            print()

        except Exception as e:
            print(f"❌ Failed pattern analysis: {e}")
            # Don't return False - this isn't critical

        print("🎉 All tests completed successfully!")
        print("\n💡 Next steps:")
        print("   - Review the saved JSON file for full response details")
        print("   - Build additional Master service methods for specific code categories")
        print("   - Add other API services (Appointments, Chart, etc.)")
        print("   - Create comprehensive unit tests")

        return True

    def test_context_manager():
        """Test using the client as a context manager."""
        print("\n🔧 Testing Context Manager Usage...")

        try:
            with NextGenClient() as client:
                print("   ✅ Client opened in context manager")

                codes = client.master.get_codes()
                print(f"   ✅ Retrieved {codes.total_count} codes")

                print("   ✅ Context manager will auto-close client")

            print("   ✅ Context manager test completed!")
            return True

        except Exception as e:
            print(f"   ❌ Context manager test failed: {e}")
            return False

    if __name__ == "__main__":
        success = True

        try:
            # Run main test
            success &= test_real_implementation()

            # Run context manager test
            success &= test_context_manager()

            if success:
                print("\n🎉 ALL TESTS PASSED! Your NextGen API integration is working perfectly! 🎉")
            else:
                print("\n❌ Some tests failed. Check the output above for details.")

        except KeyboardInterrupt:
            print("\n⚠️ Test interrupted by user")
            success = False
        except Exception as e:
            print(f"\n💥 Unexpected error: {e}")
            success = False

        sys.exit(0 if success else 1)

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\n💡 Make sure you have:")
    print("1. Installed dependencies: pip3 install -r requirements.txt")
    print("2. Created all the necessary Python files:")
    print("   - nextgen_api/models/master.py")
    print("   - nextgen_api/services/master_service.py")
    print("   - nextgen_api/client/nextgen_client.py")
    print("3. Run this script from the project root directory")
    print("4. Set up your .env file with valid credentials")
    sys.exit(1)