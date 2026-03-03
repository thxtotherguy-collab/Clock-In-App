#!/usr/bin/env python3
"""
Worker Mobile MVP Backend API Testing
Tests all auth and attendance endpoints with focus on double clock-in prevention.
"""
import requests
import sys
import json
from datetime import datetime

class WorkerMVPTester:
    def __init__(self, base_url="https://core-scaffold.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.active_entry_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 500:
                        print(f"   Response: {response_data}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw Response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_register(self):
        """Test user registration"""
        timestamp = datetime.now().strftime("%H%M%S")
        test_user = {
            "email": f"worker_{timestamp}@test.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "Worker",
            "employee_id": f"EMP_{timestamp}"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_data = response['user']
            print(f"   Registered user: {self.user_data['email']}")
            return True
        return False

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        success, _ = self.run_test(
            "Login with Invalid Credentials",
            "POST",
            "auth/login",
            401,
            data={"email": "invalid@test.com", "password": "wrongpass"}
        )
        return success

    def test_get_user_info(self):
        """Test getting current user info"""
        if not self.token:
            print("❌ Skipping - No auth token")
            return False
            
        success, response = self.run_test(
            "Get Current User Info",
            "GET",
            "auth/me",
            200
        )
        
        if success and 'user' in response:
            print(f"   User info retrieved: {response['user']['email']}")
            return True
        return False

    def test_get_today_status_initial(self):
        """Test initial today status (should not be clocked in)"""
        if not self.token:
            print("❌ Skipping - No auth token")
            return False
            
        success, response = self.run_test(
            "Get Today Status (Initial)",
            "GET",
            "attendance/today",
            200
        )
        
        if success:
            is_clocked_in = response.get('is_clocked_in', False)
            print(f"   Initially clocked in: {is_clocked_in}")
            if is_clocked_in:
                print("   ⚠️  User already clocked in - may affect double clock-in test")
            return True
        return False

    def test_clock_in(self):
        """Test clock in functionality"""
        if not self.token:
            print("❌ Skipping - No auth token")
            return False
            
        clock_in_data = {
            "method": "mobile_app",
            "gps": {
                "latitude": 37.7749,
                "longitude": -122.4194,
                "accuracy_meters": 10.0,
                "captured_at": datetime.now().isoformat() + "Z"
            }
        }
        
        success, response = self.run_test(
            "Clock In",
            "POST",
            "attendance/clock-in",
            200,
            data=clock_in_data
        )
        
        if success and 'id' in response:
            self.active_entry_id = response['id']
            print(f"   Clock in successful - Entry ID: {self.active_entry_id}")
            return True
        return False

    def test_double_clock_in_prevention(self):
        """Test double clock-in prevention (should return 409)"""
        if not self.token:
            print("❌ Skipping - No auth token")
            return False
            
        clock_in_data = {
            "method": "mobile_app",
            "gps": {
                "latitude": 37.7749,
                "longitude": -122.4194,
                "accuracy_meters": 10.0,
                "captured_at": datetime.now().isoformat() + "Z"
            }
        }
        
        success, response = self.run_test(
            "Double Clock-In Prevention",
            "POST",
            "attendance/clock-in",
            409,  # Should get conflict error
            data=clock_in_data
        )
        
        if success:
            print("   ✅ Double clock-in correctly prevented")
            return True
        return False

    def test_get_today_status_clocked_in(self):
        """Test today status while clocked in"""
        if not self.token:
            print("❌ Skipping - No auth token")
            return False
            
        success, response = self.run_test(
            "Get Today Status (Clocked In)",
            "GET",
            "attendance/today",
            200
        )
        
        if success:
            is_clocked_in = response.get('is_clocked_in', False)
            current_entry = response.get('current_entry')
            print(f"   Is clocked in: {is_clocked_in}")
            if current_entry:
                print(f"   Current entry ID: {current_entry.get('id', 'N/A')}")
            return is_clocked_in  # Should be True
        return False

    def test_clock_out(self):
        """Test clock out functionality"""
        if not self.token:
            print("❌ Skipping - No auth token")
            return False
            
        clock_out_data = {
            "method": "mobile_app",
            "break_minutes": 0,
            "gps": {
                "latitude": 37.7749,
                "longitude": -122.4194,
                "accuracy_meters": 10.0,
                "captured_at": datetime.now().isoformat() + "Z"
            }
        }
        
        success, response = self.run_test(
            "Clock Out",
            "POST",
            "attendance/clock-out",
            200,
            data=clock_out_data
        )
        
        if success and response.get('total_hours') is not None:
            total_hours = response.get('total_hours', 0)
            print(f"   Clock out successful - Total hours: {total_hours}")
            return True
        return False

    def test_clock_out_when_not_clocked_in(self):
        """Test clock out when not clocked in (should fail)"""
        if not self.token:
            print("❌ Skipping - No auth token")
            return False
            
        clock_out_data = {
            "method": "mobile_app",
            "break_minutes": 0
        }
        
        success, response = self.run_test(
            "Clock Out (Not Clocked In)",
            "POST",
            "attendance/clock-out",
            400,  # Should get bad request
            data=clock_out_data
        )
        
        if success:
            print("   ✅ Clock out correctly rejected when not clocked in")
            return True
        return False

    def test_get_week_summary(self):
        """Test week summary endpoint"""
        if not self.token:
            print("❌ Skipping - No auth token")
            return False
            
        success, response = self.run_test(
            "Get Week Summary",
            "GET",
            "attendance/week-summary",
            200
        )
        
        if success:
            total_hours = response.get('total_hours', 0)
            days_worked = response.get('days_worked', 0)
            print(f"   Week summary - Total: {total_hours}h, Days: {days_worked}")
            return True
        return False

    def test_unauthorized_access(self):
        """Test API access without token"""
        # Temporarily remove token
        original_token = self.token
        self.token = None
        
        success, _ = self.run_test(
            "Unauthorized Access (No Token)",
            "GET",
            "attendance/today",
            401
        )
        
        # Restore token
        self.token = original_token
        
        if success:
            print("   ✅ Unauthorized access correctly rejected")
            return True
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Worker Mobile MVP Backend Tests")
    print("=" * 60)
    
    tester = WorkerMVPTester()
    
    # Test sequence
    test_results = []
    
    print("\n📋 AUTHENTICATION TESTS")
    test_results.append(tester.test_register())
    test_results.append(tester.test_login_invalid_credentials())
    test_results.append(tester.test_get_user_info())
    test_results.append(tester.test_unauthorized_access())
    
    print("\n⏰ ATTENDANCE TESTS")
    test_results.append(tester.test_get_today_status_initial())
    test_results.append(tester.test_clock_in())
    test_results.append(tester.test_double_clock_in_prevention())  # Critical test
    test_results.append(tester.test_get_today_status_clocked_in())
    test_results.append(tester.test_clock_out())
    test_results.append(tester.test_clock_out_when_not_clocked_in())
    test_results.append(tester.test_get_week_summary())
    
    # Results
    print("\n" + "=" * 60)
    print(f"📊 FINAL RESULTS")
    print(f"   Tests Run: {tester.tests_run}")
    print(f"   Tests Passed: {tester.tests_passed}")
    print(f"   Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if tester.user_data:
        print(f"   Test User: {tester.user_data['email']}")
    
    # Critical features check
    critical_passed = sum(test_results)
    critical_total = len(test_results)
    print(f"   Critical Features: {critical_passed}/{critical_total}")
    
    if critical_passed == critical_total:
        print("🎉 ALL CRITICAL TESTS PASSED!")
        return 0
    else:
        print("❌ Some critical tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())