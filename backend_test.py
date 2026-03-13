"""
Backend API Testing for Phase 6 Security, Performance & Deployment Hardening

Testing focus areas:
1. Health Check Endpoints 
2. Security Headers Verification
3. Rate Limiting & Account Lockout
4. Password Policy Enforcement
5. JWT Token Revocation (Logout)
6. Change Password Functionality
"""
import requests
import json
import time
from datetime import datetime
from typing import Dict, Optional


class BackendTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api"
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        
        # Test credentials
        self.admin_creds = {
            "email": "admin@company.com", 
            "password": "Admin123!"
        }
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: dict = None):
        """Log test results."""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name}")
        if details:
            print(f"      Details: {details}")
        if not success and response_data:
            print(f"      Response: {response_data}")
        print()
    
    def authenticate_admin(self) -> bool:
        """Authenticate as admin user."""
        try:
            response = self.session.post(
                f"{self.api_url}/auth/login",
                json=self.admin_creds,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.admin_token}"
                })
                self.log_test(
                    "Admin Authentication", 
                    True, 
                    f"Successfully authenticated as {self.admin_creds['email']}"
                )
                return True
            else:
                self.log_test(
                    "Admin Authentication", 
                    False, 
                    f"Failed with status {response.status_code}",
                    response.json() if response.text else {}
                )
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_health_endpoints(self):
        """Test all health check endpoints."""
        print("🔍 TESTING HEALTH CHECK ENDPOINTS")
        print("="*50)
        
        # Test basic health endpoint
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                expected_keys = ["status", "uptime_seconds"]
                has_keys = all(key in data for key in expected_keys)
                
                self.log_test(
                    "Health Check - Basic Liveness",
                    has_keys and data.get("status") == "healthy",
                    f"Status: {data.get('status')}, Uptime: {data.get('uptime_seconds')}s",
                    data
                )
            else:
                self.log_test(
                    "Health Check - Basic Liveness",
                    False,
                    f"HTTP {response.status_code}",
                    response.json() if response.text else {}
                )
        except Exception as e:
            self.log_test("Health Check - Basic Liveness", False, f"Exception: {str(e)}")
        
        # Test readiness endpoint
        try:
            response = requests.get(f"{self.api_url}/health/ready", timeout=10)
            if response.status_code == 200:
                data = response.json()
                checks = data.get("checks", {})
                db_status = checks.get("database", {}).get("status")
                scheduler_status = checks.get("scheduler", {}).get("status")
                
                success = (
                    data.get("status") == "ready" and
                    db_status == "connected" and
                    scheduler_status == "running"
                )
                
                self.log_test(
                    "Health Check - Readiness Probe",
                    success,
                    f"Overall: {data.get('status')}, DB: {db_status}, Scheduler: {scheduler_status}",
                    data
                )
            else:
                self.log_test(
                    "Health Check - Readiness Probe",
                    False,
                    f"HTTP {response.status_code}",
                    response.json() if response.text else {}
                )
        except Exception as e:
            self.log_test("Health Check - Readiness Probe", False, f"Exception: {str(e)}")
        
        # Test deep health endpoint
        try:
            response = requests.get(f"{self.api_url}/health/deep", timeout=15)
            if response.status_code == 200:
                data = response.json()
                checks = data.get("checks", {})
                db_check = checks.get("database", {})
                memory_check = checks.get("memory", {})
                scheduler_check = checks.get("scheduler", {})
                
                has_stats = (
                    "active_users" in db_check.get("stats", {}) and
                    "memory" in checks and
                    "scheduler" in checks
                )
                
                self.log_test(
                    "Health Check - Deep Probe with Stats",
                    has_stats and data.get("status") == "healthy",
                    f"DB stats: {db_check.get('stats')}, Memory: {memory_check}, Scheduler: {scheduler_check.get('status')}",
                    data
                )
            else:
                self.log_test(
                    "Health Check - Deep Probe with Stats",
                    False,
                    f"HTTP {response.status_code}",
                    response.json() if response.text else {}
                )
        except Exception as e:
            self.log_test("Health Check - Deep Probe with Stats", False, f"Exception: {str(e)}")
    
    def test_security_headers(self):
        """Test security headers on API responses."""
        print("🔍 TESTING SECURITY HEADERS")
        print("="*50)
        
        # Test on a simple API call
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            headers = response.headers
            
            expected_headers = {
                "X-Frame-Options": "DENY",
                "X-Content-Type-Options": "nosniff", 
                "X-XSS-Protection": "1; mode=block",
                "X-Request-ID": None,  # Should exist but value varies
                "X-Process-Time": None,  # Should exist but value varies
                "Cache-Control": "no-store, no-cache, must-revalidate, private"
            }
            
            missing_headers = []
            present_headers = {}
            
            for header, expected_value in expected_headers.items():
                if header in headers:
                    present_headers[header] = headers[header]
                    if expected_value and headers[header] != expected_value:
                        missing_headers.append(f"{header} (expected '{expected_value}', got '{headers[header]}')")
                else:
                    missing_headers.append(header)
            
            success = len(missing_headers) == 0
            details = f"Present: {present_headers}"
            if missing_headers:
                details += f" | Missing/Wrong: {missing_headers}"
            
            self.log_test(
                "Security Headers Verification",
                success,
                details,
                {"headers": dict(headers)}
            )
            
        except Exception as e:
            self.log_test("Security Headers Verification", False, f"Exception: {str(e)}")
    
    def test_rate_limiting(self):
        """Test rate limiting with multiple wrong login attempts."""
        print("🔍 TESTING RATE LIMITING & ACCOUNT LOCKOUT")
        print("="*50)
        
        test_email = "admin@company.com"
        wrong_password = "WrongPassword123!"
        
        # First, test 5 wrong login attempts (should all be 401)
        for i in range(1, 6):
            try:
                response = requests.post(
                    f"{self.api_url}/auth/login",
                    json={"email": test_email, "password": wrong_password},
                    timeout=10
                )
                
                success = response.status_code == 401
                self.log_test(
                    f"Rate Limiting - Wrong Login Attempt {i}/5",
                    success,
                    f"HTTP {response.status_code} (expected 401)",
                    response.json() if response.text else {}
                )
                
                if not success:
                    break
                    
                time.sleep(0.5)  # Small delay between attempts
                
            except Exception as e:
                self.log_test(f"Rate Limiting - Wrong Login Attempt {i}/5", False, f"Exception: {str(e)}")
                break
        
        # Now test the 6th attempt (should be 429 - Too Many Requests)
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"email": test_email, "password": wrong_password},
                timeout=10
            )
            
            success = response.status_code == 429
            self.log_test(
                "Rate Limiting - 6th Wrong Attempt (Should be 429)",
                success,
                f"HTTP {response.status_code} (expected 429 - Too Many Requests)",
                response.json() if response.text else {}
            )
            
        except Exception as e:
            self.log_test("Rate Limiting - 6th Wrong Attempt (Should be 429)", False, f"Exception: {str(e)}")
        
        # Test that even correct password is blocked after lockout
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"email": test_email, "password": self.admin_creds["password"]},
                timeout=10
            )
            
            success = response.status_code == 429
            self.log_test(
                "Rate Limiting - Correct Password After Lockout (Should be 429)",
                success,
                f"HTTP {response.status_code} (expected 429 - Account locked)",
                response.json() if response.text else {}
            )
            
        except Exception as e:
            self.log_test("Rate Limiting - Correct Password After Lockout (Should be 429)", False, f"Exception: {str(e)}")
    
    def test_password_policy(self):
        """Test password policy enforcement during registration."""
        print("🔍 TESTING PASSWORD POLICY ENFORCEMENT")
        print("="*50)
        
        weak_passwords = [
            ("short", "Too short"),
            ("nouppercase1!", "No uppercase letter"),
            ("NOLOWERCASE1!", "No lowercase letter"),
            ("NoDigits!!", "No digit"),
            ("NoSpecial1", "No special character")
        ]
        
        for password, description in weak_passwords:
            try:
                response = requests.post(
                    f"{self.api_url}/auth/register",
                    json={
                        "email": f"test_{int(time.time())}@example.com",
                        "password": password,
                        "first_name": "Test",
                        "last_name": "User"
                    },
                    timeout=10
                )
                
                # Should fail with 400 due to weak password
                success = response.status_code == 400
                error_msg = ""
                if response.text:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("detail", "")
                    except:
                        error_msg = response.text
                
                self.log_test(
                    f"Password Policy - {description}",
                    success,
                    f"HTTP {response.status_code}, Error: {error_msg}",
                    response.json() if response.text else {}
                )
                
            except Exception as e:
                self.log_test(f"Password Policy - {description}", False, f"Exception: {str(e)}")
    
    def test_token_revocation_logout(self):
        """Test JWT token revocation via logout."""
        print("🔍 TESTING TOKEN REVOCATION (LOGOUT)")
        print("="*50)
        
        # First, get a fresh token
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json=self.admin_creds,
                timeout=10
            )
            
            if response.status_code != 200:
                self.log_test("Token Revocation - Get Fresh Token", False, f"Login failed: HTTP {response.status_code}")
                return
                
            token_data = response.json()
            test_token = token_data["access_token"]
            
            # Test logout (should succeed)
            logout_response = requests.post(
                f"{self.api_url}/auth/logout",
                headers={"Authorization": f"Bearer {test_token}"},
                timeout=10
            )
            
            logout_success = logout_response.status_code == 200
            self.log_test(
                "Token Revocation - Logout Request",
                logout_success,
                f"HTTP {logout_response.status_code}",
                logout_response.json() if logout_response.text else {}
            )
            
            # Now try to use the same token (should fail with 401)
            if logout_success:
                test_response = requests.get(
                    f"{self.api_url}/auth/me",
                    headers={"Authorization": f"Bearer {test_token}"},
                    timeout=10
                )
                
                revoke_success = test_response.status_code == 401
                self.log_test(
                    "Token Revocation - Use Revoked Token (Should Fail)",
                    revoke_success,
                    f"HTTP {test_response.status_code} (expected 401)",
                    test_response.json() if test_response.text else {}
                )
                
        except Exception as e:
            self.log_test("Token Revocation - Logout", False, f"Exception: {str(e)}")
    
    def test_change_password(self):
        """Test change password functionality with policy validation."""
        print("🔍 TESTING CHANGE PASSWORD")
        print("="*50)
        
        # Ensure we have a valid token
        if not self.admin_token:
            if not self.authenticate_admin():
                self.log_test("Change Password - Authentication Required", False, "Could not authenticate admin")
                return
        
        # Test changing password to a new valid password
        new_password = "NewAdmin456!"
        try:
            response = self.session.post(
                f"{self.api_url}/auth/change-password",
                json={
                    "current_password": self.admin_creds["password"],
                    "new_password": new_password
                },
                timeout=10
            )
            
            change_success = response.status_code == 200
            self.log_test(
                "Change Password - Valid New Password",
                change_success,
                f"HTTP {response.status_code}",
                response.json() if response.text else {}
            )
            
            if change_success:
                # Test login with new password
                login_response = requests.post(
                    f"{self.api_url}/auth/login",
                    json={"email": self.admin_creds["email"], "password": new_password},
                    timeout=10
                )
                
                new_login_success = login_response.status_code == 200
                self.log_test(
                    "Change Password - Login with New Password",
                    new_login_success,
                    f"HTTP {login_response.status_code}",
                    login_response.json() if login_response.text else {}
                )
                
                # Change back to original password
                if new_login_success:
                    new_token = login_response.json()["access_token"]
                    restore_response = requests.post(
                        f"{self.api_url}/auth/change-password",
                        json={
                            "current_password": new_password,
                            "new_password": self.admin_creds["password"]
                        },
                        headers={"Authorization": f"Bearer {new_token}"},
                        timeout=10
                    )
                    
                    restore_success = restore_response.status_code == 200
                    self.log_test(
                        "Change Password - Restore Original Password",
                        restore_success,
                        f"HTTP {restore_response.status_code}",
                        restore_response.json() if restore_response.text else {}
                    )
                    
        except Exception as e:
            self.log_test("Change Password", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all Phase 6 security tests."""
        print("🚀 STARTING PHASE 6 SECURITY TESTING")
        print("="*60)
        print(f"Backend URL: {self.api_url}")
        print(f"Test Started: {datetime.now().isoformat()}")
        print("="*60)
        print()
        
        # Authenticate first
        if not self.authenticate_admin():
            print("❌ Cannot proceed without authentication")
            return
        
        # Run all test suites
        self.test_health_endpoints()
        self.test_security_headers()
        self.test_rate_limiting()
        self.test_password_policy()
        self.test_token_revocation_logout()
        self.test_change_password()
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("="*60)
        print("📊 PHASE 6 SECURITY TESTING SUMMARY")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print()
        
        # List failures
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"   • {test['test']}: {test['details']}")
            print()
        
        print(f"Test Completed: {datetime.now().isoformat()}")
        print("="*60)


if __name__ == "__main__":
    # Read backend URL from environment
    backend_url = "https://timesheet-dashboard-4.preview.emergentagent.com"
    
    print(f"Phase 6 Security Testing")
    print(f"Backend URL: {backend_url}/api")
    print()
    
    tester = BackendTester(backend_url)
    tester.run_all_tests()