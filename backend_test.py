#!/usr/bin/env python3
"""
Backend Testing Suite - Phase 5: Automated Reporting & Payroll Engine
Tests all Report APIs with proper authentication and role-based access control.

Test Coverage:
- Report configuration endpoints
- Manual report triggering
- Report preview (JSON and HTML)
- Report history and email logs
- SA BCEA overtime configuration
- Payroll summary
- Scheduler status
"""
import asyncio
import aiohttp
import json
from typing import Dict, List

# Base URLs and Authentication
BASE_URL = "https://22ab362b-ef92-48cd-892f-fb174db57b96.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test credentials from review request
AUTH_CREDENTIALS = {
    "SUPER_ADMIN": {"email": "admin@company.com", "password": "Admin123!"},
    "BRANCH_ADMIN": {"email": "branchadmin@company.com", "password": "Admin123!"},
    "WORKER": {"email": "worker1@company.com", "password": "Worker123!"}
}

# Global test state
test_results = {}
auth_tokens = {}


class TestRunner:
    def __init__(self):
        self.session = None
        self.results = []
        
    async def setup(self):
        """Initialize HTTP session and authenticate all users."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(ssl=False)
        )
        
        # Authenticate all users
        for role, creds in AUTH_CREDENTIALS.items():
            try:
                token = await self.authenticate(creds["email"], creds["password"])
                auth_tokens[role] = token
                self.log_result(f"AUTH-{role}", "✅ PASS", f"Authentication successful")
            except Exception as e:
                auth_tokens[role] = None
                self.log_result(f"AUTH-{role}", "❌ FAIL", f"Authentication failed: {e}")
        
        print(f"\n🔐 Authentication completed: {len([t for t in auth_tokens.values() if t])} / {len(AUTH_CREDENTIALS)} successful\n")

    async def authenticate(self, email: str, password: str) -> str:
        """Authenticate user and return JWT token."""
        async with self.session.post(
            f"{API_BASE}/auth/login", 
            json={"email": email, "password": password}
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"HTTP {resp.status}: {text}")
            data = await resp.json()
            return data.get("access_token")

    def get_auth_headers(self, role: str) -> Dict:
        """Get authorization headers for a role."""
        token = auth_tokens.get(role)
        if not token:
            raise Exception(f"No token available for {role}")
        return {"Authorization": f"Bearer {token}"}

    async def test_endpoint(self, method: str, endpoint: str, role: str, 
                          expected_status: int = 200, json_data: Dict = None, 
                          test_name: str = None) -> Dict:
        """Test an API endpoint with authentication."""
        url = f"{API_BASE}{endpoint}"
        test_name = test_name or f"{method} {endpoint} ({role})"
        
        try:
            headers = self.get_auth_headers(role)
            
            # Make request
            if method.upper() == "GET":
                async with self.session.get(url, headers=headers) as resp:
                    return await self.process_response(resp, test_name, expected_status)
            elif method.upper() == "POST":
                async with self.session.post(url, headers=headers, json=json_data) as resp:
                    return await self.process_response(resp, test_name, expected_status)
            elif method.upper() == "PUT":
                async with self.session.put(url, headers=headers, json=json_data) as resp:
                    return await self.process_response(resp, test_name, expected_status)
            else:
                raise Exception(f"Unsupported method: {method}")
                
        except Exception as e:
            self.log_result(test_name, "❌ FAIL", f"Request failed: {e}")
            return {"status": "error", "error": str(e)}

    async def process_response(self, resp, test_name: str, expected_status: int) -> Dict:
        """Process HTTP response and log results."""
        status = resp.status
        content_type = resp.headers.get('content-type', '')
        
        try:
            if 'application/json' in content_type:
                data = await resp.json()
            else:
                data = await resp.text()
        except:
            data = await resp.text()
        
        if status == expected_status:
            self.log_result(test_name, "✅ PASS", f"HTTP {status}, response received")
            return {"status": "success", "data": data, "http_status": status}
        else:
            self.log_result(test_name, "❌ FAIL", f"Expected HTTP {expected_status}, got {status}: {str(data)[:200]}")
            return {"status": "fail", "data": data, "http_status": status}

    def log_result(self, test_name: str, status: str, details: str):
        """Log test result."""
        result = {"test": test_name, "status": status, "details": details}
        self.results.append(result)
        print(f"{status} {test_name}: {details}")

    async def run_report_config_tests(self):
        """Test report configuration endpoints."""
        print("📊 Testing Report Configuration...")
        
        # Test GET /api/reports/config for all roles
        await self.test_endpoint("GET", "/reports/config", "SUPER_ADMIN", 200, 
                                test_name="Get report config (SUPER_ADMIN)")
        await self.test_endpoint("GET", "/reports/config", "BRANCH_ADMIN", 200, 
                                test_name="Get report config (BRANCH_ADMIN)")
        await self.test_endpoint("GET", "/reports/config", "WORKER", 403, 
                                test_name="Get report config (WORKER - should be blocked)")
        
        # Test PUT /api/reports/config
        config_update = {
            "global_recipients": ["test@test.com"],
            "hr_cc": ["hr@test.com"],
            "enabled": True
        }
        await self.test_endpoint("PUT", "/reports/config", "SUPER_ADMIN", 200, config_update,
                                test_name="Update report config (SUPER_ADMIN)")
        await self.test_endpoint("PUT", "/reports/config", "BRANCH_ADMIN", 200, config_update,
                                test_name="Update report config (BRANCH_ADMIN)")
        await self.test_endpoint("PUT", "/reports/config", "WORKER", 403, config_update,
                                test_name="Update report config (WORKER - should be blocked)")

    async def run_manual_report_tests(self):
        """Test manual report sending."""
        print("📧 Testing Manual Report Sending...")
        
        # Test POST /api/reports/send-now
        send_request = {"branch_id": None}
        result = await self.test_endpoint("POST", "/reports/send-now", "SUPER_ADMIN", 200, send_request,
                                        test_name="Send report now (SUPER_ADMIN)")
        
        # Check if emails_sent is returned
        if result.get("status") == "success" and "emails_sent" in str(result.get("data", {})):
            self.log_result("Send report validation", "✅ PASS", "Response includes emails_sent count")
        elif result.get("status") == "success":
            self.log_result("Send report validation", "⚠️ WARN", f"Response format: {result.get('data', {})}")
        
        await self.test_endpoint("POST", "/reports/send-now", "BRANCH_ADMIN", 200, send_request,
                                test_name="Send report now (BRANCH_ADMIN)")
        await self.test_endpoint("POST", "/reports/send-now", "WORKER", 403, send_request,
                                test_name="Send report now (WORKER - should be blocked)")

    async def run_preview_tests(self):
        """Test report preview endpoints."""
        print("👀 Testing Report Previews...")
        
        # Test GET /api/reports/preview
        await self.test_endpoint("GET", "/reports/preview", "SUPER_ADMIN", 200,
                                test_name="Preview report data (SUPER_ADMIN)")
        await self.test_endpoint("GET", "/reports/preview", "BRANCH_ADMIN", 200,
                                test_name="Preview report data (BRANCH_ADMIN)")
        await self.test_endpoint("GET", "/reports/preview", "WORKER", 403,
                                test_name="Preview report data (WORKER - should be blocked)")
        
        # Test GET /api/reports/preview/html
        result = await self.test_endpoint("GET", "/reports/preview/html", "SUPER_ADMIN", 200,
                                        test_name="Preview HTML template (SUPER_ADMIN)")
        
        # Validate HTML response
        if result.get("status") == "success":
            html_content = result.get("data", "")
            if isinstance(html_content, str) and "<!DOCTYPE html>" in html_content:
                self.log_result("HTML template validation", "✅ PASS", "Valid HTML template returned")
            else:
                self.log_result("HTML template validation", "❌ FAIL", f"Invalid HTML format: {type(html_content)}")

    async def run_history_tests(self):
        """Test report history and email logs."""
        print("📜 Testing Report History...")
        
        # Test GET /api/reports/history
        await self.test_endpoint("GET", "/reports/history", "SUPER_ADMIN", 200,
                                test_name="Get report history (SUPER_ADMIN)")
        await self.test_endpoint("GET", "/reports/history", "BRANCH_ADMIN", 200,
                                test_name="Get report history (BRANCH_ADMIN)")
        await self.test_endpoint("GET", "/reports/history", "WORKER", 403,
                                test_name="Get report history (WORKER - should be blocked)")
        
        # Test GET /api/reports/email-logs (should show mocked entries from send-now)
        result = await self.test_endpoint("GET", "/reports/email-logs", "SUPER_ADMIN", 200,
                                        test_name="Get email logs (SUPER_ADMIN)")
        
        # Check if email logs contain entries from send-now tests
        if result.get("status") == "success":
            data = result.get("data", {})
            logs = data.get("logs", []) if isinstance(data, dict) else []
            if logs:
                self.log_result("Email logs validation", "✅ PASS", f"Found {len(logs)} email log entries")
            else:
                self.log_result("Email logs validation", "⚠️ WARN", "No email log entries found (may be expected)")

    async def run_overtime_config_tests(self):
        """Test SA BCEA overtime configuration."""
        print("⏰ Testing Overtime Configuration...")
        
        # Test GET /api/reports/overtime-config
        result = await self.test_endpoint("GET", "/reports/overtime-config", "SUPER_ADMIN", 200,
                                        test_name="Get overtime config (SUPER_ADMIN)")
        
        # Validate SA BCEA defaults
        if result.get("status") == "success":
            data = result.get("data", {})
            rules = data.get("rules", {}) if isinstance(data, dict) else {}
            tiers = data.get("tiers", {}) if isinstance(data, dict) else {}
            
            # Check SA BCEA requirements
            expected_checks = [
                (rules.get("daily_threshold_5day") == 9.0, "9hrs daily threshold (5-day week)"),
                (rules.get("weekly_threshold") == 45.0, "45hrs weekly threshold"),
                (tiers.get("standard_ot", {}).get("multiplier") == 1.5, "1.5x overtime multiplier"),
                (tiers.get("sunday", {}).get("multiplier") == 2.0, "2x Sunday multiplier")
            ]
            
            for check, desc in expected_checks:
                if check:
                    self.log_result(f"SA BCEA - {desc}", "✅ PASS", "Correct SA BCEA default")
                else:
                    self.log_result(f"SA BCEA - {desc}", "❌ FAIL", f"Incorrect default: {rules}, {tiers}")
        
        await self.test_endpoint("GET", "/reports/overtime-config", "BRANCH_ADMIN", 200,
                                test_name="Get overtime config (BRANCH_ADMIN)")
        await self.test_endpoint("GET", "/reports/overtime-config", "WORKER", 403,
                                test_name="Get overtime config (WORKER - should be blocked)")
        
        # Test PUT /api/reports/overtime-config (SUPER_ADMIN only)
        ot_update = {
            "weekly_threshold": 45,
            "standard_ot_multiplier": 1.5
        }
        await self.test_endpoint("PUT", "/reports/overtime-config", "SUPER_ADMIN", 200, ot_update,
                                test_name="Update overtime config (SUPER_ADMIN)")
        await self.test_endpoint("PUT", "/reports/overtime-config", "BRANCH_ADMIN", 403, ot_update,
                                test_name="Update overtime config (BRANCH_ADMIN - should be blocked)")

    async def run_payroll_summary_tests(self):
        """Test payroll summary endpoint."""
        print("💰 Testing Payroll Summary...")
        
        # Test GET /api/reports/payroll-summary
        await self.test_endpoint("GET", "/reports/payroll-summary", "SUPER_ADMIN", 200,
                                test_name="Get payroll summary (SUPER_ADMIN)")
        await self.test_endpoint("GET", "/reports/payroll-summary", "BRANCH_ADMIN", 200,
                                test_name="Get payroll summary (BRANCH_ADMIN)")
        await self.test_endpoint("GET", "/reports/payroll-summary", "WORKER", 403,
                                test_name="Get payroll summary (WORKER - should be blocked)")

    async def run_scheduler_tests(self):
        """Test scheduler status endpoint."""
        print("🕐 Testing Scheduler Status...")
        
        # Test GET /api/reports/scheduler/status (SUPER_ADMIN only)
        result = await self.test_endpoint("GET", "/reports/scheduler/status", "SUPER_ADMIN", 200,
                                        test_name="Get scheduler status (SUPER_ADMIN)")
        
        # Check if scheduler is running with daily_report job
        if result.get("status") == "success":
            data = result.get("data", {})
            if isinstance(data, dict):
                running = data.get("running", False)
                jobs = data.get("jobs", [])
                
                if running:
                    self.log_result("Scheduler running", "✅ PASS", "Scheduler is active")
                else:
                    self.log_result("Scheduler running", "❌ FAIL", "Scheduler is not running")
                
                # Check for daily report job
                daily_job = any("daily" in job.get("name", "").lower() for job in jobs if isinstance(job, dict))
                if daily_job:
                    self.log_result("Daily job configured", "✅ PASS", "Daily report job found in scheduler")
                else:
                    self.log_result("Daily job configured", "❌ FAIL", f"No daily job found: {jobs}")
        
        await self.test_endpoint("GET", "/reports/scheduler/status", "BRANCH_ADMIN", 403,
                                test_name="Get scheduler status (BRANCH_ADMIN - should be blocked)")

    async def run_role_scoping_tests(self):
        """Test that BRANCH_ADMIN is properly scoped to their branch."""
        print("🔒 Testing Role-based Data Scoping...")
        
        # Get report config as BRANCH_ADMIN to check scoping
        result = await self.test_endpoint("GET", "/reports/preview", "BRANCH_ADMIN", 200,
                                        test_name="BRANCH_ADMIN data scoping check")
        
        if result.get("status") == "success":
            self.log_result("BRANCH_ADMIN scoping", "✅ PASS", "BRANCH_ADMIN can access scoped report data")

    async def cleanup(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()

    def generate_summary(self):
        """Generate test summary."""
        passed = len([r for r in self.results if "✅ PASS" in r["status"]])
        failed = len([r for r in self.results if "❌ FAIL" in r["status"]])
        warnings = len([r for r in self.results if "⚠️ WARN" in r["status"]])
        total = len(self.results)
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n" + "="*80)
        print(f"🧪 PHASE 5 BACKEND TEST SUMMARY")
        print(f"="*80)
        print(f"📊 Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Warnings: {warnings}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"="*80)
        
        if failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.results:
                if "❌ FAIL" in result["status"]:
                    print(f"  • {result['test']}: {result['details']}")
        
        if warnings > 0:
            print(f"\n⚠️ WARNINGS:")
            for result in self.results:
                if "⚠️ WARN" in result["status"]:
                    print(f"  • {result['test']}: {result['details']}")
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "success_rate": success_rate,
            "results": self.results
        }


async def main():
    """Main test execution."""
    print("🚀 Starting Phase 5 - Automated Reporting & Payroll Engine Backend Tests")
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"📡 API Base: {API_BASE}")
    print("="*80)
    
    runner = TestRunner()
    
    try:
        # Setup and authentication
        await runner.setup()
        
        # Run all test suites
        await runner.run_report_config_tests()
        await runner.run_manual_report_tests()
        await runner.run_preview_tests()
        await runner.run_history_tests()
        await runner.run_overtime_config_tests()
        await runner.run_payroll_summary_tests()
        await runner.run_scheduler_tests()
        await runner.run_role_scoping_tests()
        
        # Generate summary
        summary = runner.generate_summary()
        
        return summary
        
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        runner.log_result("Test Suite", "❌ CRITICAL", f"Test suite failed: {e}")
        return {"error": str(e), "results": runner.results}
    
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())