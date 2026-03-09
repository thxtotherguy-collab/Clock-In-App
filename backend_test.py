#!/usr/bin/env python3
"""
Phase 4 Admin Dashboard MVP Backend API Testing
Tests all critical endpoints with different role-based access controls.
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

# Base URL from environment
BASE_URL = "https://22ab362b-ef92-48cd-892f-fb174db57b96.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test credentials
TEST_USERS = {
    "SUPER_ADMIN": {"email": "admin@company.com", "password": "Admin123!"},
    "BRANCH_ADMIN": {"email": "branchadmin@company.com", "password": "Admin123!"},
    "WORKER": {"email": "worker1@company.com", "password": "Worker123!"}
}

class APITestRunner:
    def __init__(self):
        self.tokens = {}
        self.test_results = {}
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Backend-Test-Suite/1.0'
        })

    def login_user(self, role: str) -> Dict[str, Any]:
        """Login a user and store the token."""
        print(f"🔐 Logging in as {role}...")
        
        user_creds = TEST_USERS[role]
        login_data = {
            "email": user_creds["email"],
            "password": user_creds["password"]
        }
        
        try:
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.tokens[role] = {
                    "access_token": data["access_token"],
                    "user": data["user"]
                }
                print(f"✅ {role} login successful")
                return data
            else:
                print(f"❌ {role} login failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ {role} login error: {str(e)}")
            return None

    def make_authenticated_request(self, method: str, endpoint: str, role: str, **kwargs) -> requests.Response:
        """Make an authenticated request."""
        if role not in self.tokens:
            raise ValueError(f"No token found for role {role}")
        
        headers = {
            "Authorization": f"Bearer {self.tokens[role]['access_token']}"
        }
        
        url = f"{API_BASE}{endpoint}"
        
        try:
            response = self.session.request(method, url, headers=headers, **kwargs)
            return response
        except Exception as e:
            print(f"❌ Request failed: {str(e)}")
            raise

    def test_dashboard_overview(self, role: str) -> Dict[str, Any]:
        """Test dashboard overview endpoint."""
        print(f"\n📊 Testing Dashboard Overview as {role}")
        
        try:
            # Test basic overview
            response = self.make_authenticated_request("GET", "/admin/dashboard/overview", role)
            
            result = {
                "endpoint": "/admin/dashboard/overview",
                "role": role,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "data": None,
                "error": None
            }
            
            if response.status_code == 200:
                data = response.json()
                result["data"] = data
                print(f"✅ Overview data received: {data.get('total_workers', 0)} workers, {data.get('total_hours_today', 0)} hours")
                
                # Test with branch filter if SUPER_ADMIN
                if role == "SUPER_ADMIN":
                    response_with_branch = self.make_authenticated_request(
                        "GET", "/admin/dashboard/overview", role, params={"branch_id": "test_branch"}
                    )
                    print(f"   Branch filter test: {response_with_branch.status_code}")
                    
            elif response.status_code == 403:
                result["error"] = "Forbidden - Expected for WORKER role"
                print(f"🔒 Access denied (expected for WORKER): {response.status_code}")
            else:
                result["error"] = response.text
                print(f"❌ Failed: {response.status_code} - {response.text}")
            
            return result
            
        except Exception as e:
            return {
                "endpoint": "/admin/dashboard/overview",
                "role": role,
                "status_code": 500,
                "success": False,
                "error": str(e)
            }

    def test_live_status(self, role: str) -> Dict[str, Any]:
        """Test live status endpoint."""
        print(f"\n👥 Testing Live Status as {role}")
        
        try:
            response = self.make_authenticated_request("GET", "/admin/dashboard/live-status", role)
            
            result = {
                "endpoint": "/admin/dashboard/live-status",
                "role": role,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "data": None,
                "error": None
            }
            
            if response.status_code == 200:
                data = response.json()
                result["data"] = data
                print(f"✅ Live status: {data.get('count', 0)} active workers")
            elif response.status_code == 403:
                result["error"] = "Forbidden - Expected for WORKER role"
                print(f"🔒 Access denied (expected for WORKER): {response.status_code}")
            else:
                result["error"] = response.text
                print(f"❌ Failed: {response.status_code} - {response.text}")
            
            return result
            
        except Exception as e:
            return {
                "endpoint": "/admin/dashboard/live-status", 
                "role": role,
                "status_code": 500,
                "success": False,
                "error": str(e)
            }

    def test_users_list(self, role: str) -> Dict[str, Any]:
        """Test users list endpoint."""
        print(f"\n👤 Testing Users List as {role}")
        
        try:
            response = self.make_authenticated_request("GET", "/admin/users/list", role)
            
            result = {
                "endpoint": "/admin/users/list",
                "role": role,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "data": None,
                "error": None
            }
            
            if response.status_code == 200:
                data = response.json()
                result["data"] = data
                print(f"✅ Users list: {data.get('total', 0)} users, page {data.get('page', 1)}")
                
                # Test search functionality
                search_response = self.make_authenticated_request(
                    "GET", "/admin/users/list", role, params={"search": "admin"}
                )
                print(f"   Search test: {search_response.status_code}")
                
            elif response.status_code == 403:
                result["error"] = "Forbidden - Expected for WORKER role"
                print(f"🔒 Access denied (expected for WORKER): {response.status_code}")
            else:
                result["error"] = response.text
                print(f"❌ Failed: {response.status_code} - {response.text}")
            
            return result
            
        except Exception as e:
            return {
                "endpoint": "/admin/users/list",
                "role": role, 
                "status_code": 500,
                "success": False,
                "error": str(e)
            }

    def test_branches_list(self, role: str) -> Dict[str, Any]:
        """Test branches list endpoint."""
        print(f"\n🏢 Testing Branches List as {role}")
        
        try:
            response = self.make_authenticated_request("GET", "/admin/branches/list", role)
            
            result = {
                "endpoint": "/admin/branches/list",
                "role": role,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "data": None,
                "error": None
            }
            
            if response.status_code == 200:
                data = response.json()
                result["data"] = data
                print(f"✅ Branches list: {len(data.get('branches', []))} branches")
            elif response.status_code == 403:
                result["error"] = "Forbidden - Expected for WORKER role"
                print(f"🔒 Access denied (expected for WORKER): {response.status_code}")
            else:
                result["error"] = response.text
                print(f"❌ Failed: {response.status_code} - {response.text}")
            
            return result
            
        except Exception as e:
            return {
                "endpoint": "/admin/branches/list",
                "role": role,
                "status_code": 500,
                "success": False,
                "error": str(e)
            }

    def test_time_entries_pending(self, role: str) -> Dict[str, Any]:
        """Test pending time entries endpoint."""
        print(f"\n⏰ Testing Time Entries Pending as {role}")
        
        try:
            response = self.make_authenticated_request("GET", "/admin/time-entries/pending-approval", role)
            
            result = {
                "endpoint": "/admin/time-entries/pending-approval",
                "role": role,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "data": None,
                "error": None
            }
            
            if response.status_code == 200:
                data = response.json()
                result["data"] = data
                print(f"✅ Pending entries: {data.get('total', 0)} entries")
            elif response.status_code == 403:
                result["error"] = "Forbidden - Expected for WORKER role"
                print(f"🔒 Access denied (expected for WORKER): {response.status_code}")
            else:
                result["error"] = response.text
                print(f"❌ Failed: {response.status_code} - {response.text}")
            
            return result
            
        except Exception as e:
            return {
                "endpoint": "/admin/time-entries/pending-approval",
                "role": role,
                "status_code": 500,
                "success": False,
                "error": str(e)
            }

    def test_csv_exports(self, role: str) -> Dict[str, Any]:
        """Test CSV export endpoints."""
        print(f"\n📄 Testing CSV Exports as {role}")
        
        results = []
        
        # Test timesheet CSV
        try:
            response = self.make_authenticated_request("GET", "/exports/timesheet/csv", role)
            
            result = {
                "endpoint": "/exports/timesheet/csv",
                "role": role,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "content_type": response.headers.get('content-type', ''),
                "error": None
            }
            
            if response.status_code == 200:
                print(f"✅ Timesheet CSV export successful ({len(response.content)} bytes)")
                # Check if it's actually CSV
                if 'text/csv' in response.headers.get('content-type', ''):
                    result["is_csv"] = True
                else:
                    result["is_csv"] = False
                    print("⚠️  Content type is not CSV")
            elif response.status_code == 403:
                result["error"] = "Forbidden - Expected for WORKER role"
                print(f"🔒 Access denied (expected for WORKER): {response.status_code}")
            else:
                result["error"] = response.text
                print(f"❌ Timesheet CSV failed: {response.status_code}")
                
            results.append(result)
            
        except Exception as e:
            results.append({
                "endpoint": "/exports/timesheet/csv",
                "role": role,
                "status_code": 500,
                "success": False,
                "error": str(e)
            })
        
        # Test payroll CSV
        try:
            response = self.make_authenticated_request("GET", "/exports/payroll/csv", role)
            
            result = {
                "endpoint": "/exports/payroll/csv",
                "role": role,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "content_type": response.headers.get('content-type', ''),
                "error": None
            }
            
            if response.status_code == 200:
                print(f"✅ Payroll CSV export successful ({len(response.content)} bytes)")
                if 'text/csv' in response.headers.get('content-type', ''):
                    result["is_csv"] = True
                else:
                    result["is_csv"] = False
                    print("⚠️  Content type is not CSV")
            elif response.status_code == 403:
                result["error"] = "Forbidden - Expected for WORKER role"
                print(f"🔒 Access denied (expected for WORKER): {response.status_code}")
            else:
                result["error"] = response.text
                print(f"❌ Payroll CSV failed: {response.status_code}")
                
            results.append(result)
            
        except Exception as e:
            results.append({
                "endpoint": "/exports/payroll/csv",
                "role": role,
                "status_code": 500,
                "success": False,
                "error": str(e)
            })
        
        return results

    def test_excel_exports(self, role: str) -> Dict[str, Any]:
        """Test Excel export endpoints."""
        print(f"\n📊 Testing Excel Exports as {role}")
        
        results = []
        
        # Test payroll Excel
        try:
            response = self.make_authenticated_request("GET", "/exports/payroll/excel", role)
            
            result = {
                "endpoint": "/exports/payroll/excel",
                "role": role,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "content_type": response.headers.get('content-type', ''),
                "error": None
            }
            
            if response.status_code == 200:
                print(f"✅ Payroll Excel export successful ({len(response.content)} bytes)")
                # Check if it's actually Excel
                if 'spreadsheetml' in response.headers.get('content-type', ''):
                    result["is_excel"] = True
                else:
                    result["is_excel"] = False
                    print("⚠️  Content type is not Excel")
            elif response.status_code == 403:
                result["error"] = "Forbidden - Expected for WORKER role"
                print(f"🔒 Access denied (expected for WORKER): {response.status_code}")
            else:
                result["error"] = response.text
                print(f"❌ Payroll Excel failed: {response.status_code}")
                
            results.append(result)
            
        except Exception as e:
            results.append({
                "endpoint": "/exports/payroll/excel",
                "role": role,
                "status_code": 500,
                "success": False,
                "error": str(e)
            })
        
        # Test timesheet Excel
        try:
            response = self.make_authenticated_request("GET", "/exports/timesheet/excel", role)
            
            result = {
                "endpoint": "/exports/timesheet/excel",
                "role": role,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "content_type": response.headers.get('content-type', ''),
                "error": None
            }
            
            if response.status_code == 200:
                print(f"✅ Timesheet Excel export successful ({len(response.content)} bytes)")
                if 'spreadsheetml' in response.headers.get('content-type', ''):
                    result["is_excel"] = True
                else:
                    result["is_excel"] = False
                    print("⚠️  Content type is not Excel")
            elif response.status_code == 403:
                result["error"] = "Forbidden - Expected for WORKER role"
                print(f"🔒 Access denied (expected for WORKER): {response.status_code}")
            else:
                result["error"] = response.text
                print(f"❌ Timesheet Excel failed: {response.status_code}")
                
            results.append(result)
            
        except Exception as e:
            results.append({
                "endpoint": "/exports/timesheet/excel",
                "role": role,
                "status_code": 500,
                "success": False,
                "error": str(e)
            })
        
        return results

    def test_audit_logs(self, role: str) -> Dict[str, Any]:
        """Test audit logs endpoints."""
        print(f"\n📋 Testing Audit Logs as {role}")
        
        results = []
        
        # Test audit logs list
        try:
            response = self.make_authenticated_request("GET", "/admin/audit-logs/list", role)
            
            result = {
                "endpoint": "/admin/audit-logs/list",
                "role": role,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "data": None,
                "error": None
            }
            
            if response.status_code == 200:
                data = response.json()
                result["data"] = data
                print(f"✅ Audit logs list: {data.get('total', 0)} logs")
            elif response.status_code == 403:
                result["error"] = "Forbidden - Expected for WORKER role"
                print(f"🔒 Access denied (expected for WORKER): {response.status_code}")
            else:
                result["error"] = response.text
                print(f"❌ Audit logs list failed: {response.status_code}")
                
            results.append(result)
            
        except Exception as e:
            results.append({
                "endpoint": "/admin/audit-logs/list",
                "role": role,
                "status_code": 500,
                "success": False,
                "error": str(e)
            })
        
        # Test audit categories
        try:
            response = self.make_authenticated_request("GET", "/admin/audit-logs/categories", role)
            
            result = {
                "endpoint": "/admin/audit-logs/categories",
                "role": role,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "data": None,
                "error": None
            }
            
            if response.status_code == 200:
                data = response.json()
                result["data"] = data
                print(f"✅ Audit categories: {len(data.get('categories', []))} categories")
            elif response.status_code == 403:
                result["error"] = "Forbidden - Expected for WORKER role"
                print(f"🔒 Access denied (expected for WORKER): {response.status_code}")
            else:
                result["error"] = response.text
                print(f"❌ Audit categories failed: {response.status_code}")
                
            results.append(result)
            
        except Exception as e:
            results.append({
                "endpoint": "/admin/audit-logs/categories",
                "role": role,
                "status_code": 500,
                "success": False,
                "error": str(e)
            })
        
        return results

    def run_comprehensive_test(self):
        """Run comprehensive API tests for all roles."""
        print("=" * 80)
        print("🚀 PHASE 4 ADMIN DASHBOARD MVP - BACKEND API TESTING")
        print("=" * 80)
        
        # Login all users first
        for role in TEST_USERS.keys():
            login_result = self.login_user(role)
            if not login_result:
                print(f"❌ Failed to login {role} - skipping tests")
                continue
        
        # Test all endpoints for each role
        for role in self.tokens.keys():
            print(f"\n" + "="*60)
            print(f"🧪 TESTING ALL ENDPOINTS AS {role}")
            print("="*60)
            
            # Dashboard Overview
            self.test_results[f"dashboard_overview_{role}"] = self.test_dashboard_overview(role)
            
            # Live Status
            self.test_results[f"live_status_{role}"] = self.test_live_status(role)
            
            # Users List
            self.test_results[f"users_list_{role}"] = self.test_users_list(role)
            
            # Branches List
            self.test_results[f"branches_list_{role}"] = self.test_branches_list(role)
            
            # Time Entries Pending
            self.test_results[f"time_entries_pending_{role}"] = self.test_time_entries_pending(role)
            
            # CSV Exports
            csv_results = self.test_csv_exports(role)
            for i, result in enumerate(csv_results):
                self.test_results[f"csv_export_{i}_{role}"] = result
            
            # Excel Exports
            excel_results = self.test_excel_exports(role)
            for i, result in enumerate(excel_results):
                self.test_results[f"excel_export_{i}_{role}"] = result
            
            # Audit Logs
            audit_results = self.test_audit_logs(role)
            for i, result in enumerate(audit_results):
                self.test_results[f"audit_logs_{i}_{role}"] = result

    def generate_summary(self):
        """Generate test summary."""
        print("\n" + "="*80)
        print("📊 TEST RESULTS SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results.values() if r.get("success", False)])
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {(successful_tests/total_tests*100):.1f}%")
        
        print("\n🟢 SUCCESSFUL TESTS:")
        for test_name, result in self.test_results.items():
            if result.get("success", False):
                print(f"   ✅ {test_name}: {result['endpoint']} ({result['role']})")
        
        print("\n🔴 FAILED TESTS:")
        failed_count = 0
        for test_name, result in self.test_results.items():
            if not result.get("success", False):
                failed_count += 1
                error_msg = result.get("error", "Unknown error")
                if "Forbidden" in error_msg and result.get("role") == "WORKER":
                    print(f"   🔒 {test_name}: {result['endpoint']} - Access correctly restricted for WORKER")
                else:
                    print(f"   ❌ {test_name}: {result['endpoint']} ({result['role']}) - {error_msg}")
        
        print(f"\n📈 ANALYSIS:")
        
        # Check role-based access control
        super_admin_success = len([r for k, r in self.test_results.items() if "SUPER_ADMIN" in k and r.get("success", False)])
        branch_admin_success = len([r for k, r in self.test_results.items() if "BRANCH_ADMIN" in k and r.get("success", False)])
        worker_forbidden = len([r for k, r in self.test_results.items() if "WORKER" in k and r.get("status_code") == 403])
        
        print(f"   🎯 SUPER_ADMIN successful operations: {super_admin_success}")
        print(f"   🏢 BRANCH_ADMIN successful operations: {branch_admin_success}")
        print(f"   🔒 WORKER correctly blocked operations: {worker_forbidden}")
        
        # Check export functionality
        excel_exports = [r for k, r in self.test_results.items() if "excel_export" in k and r.get("success", False)]
        csv_exports = [r for k, r in self.test_results.items() if "csv_export" in k and r.get("success", False)]
        
        print(f"   📊 Excel exports working: {len(excel_exports)}")
        print(f"   📄 CSV exports working: {len(csv_exports)}")
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": successful_tests/total_tests*100,
            "super_admin_success": super_admin_success,
            "branch_admin_success": branch_admin_success,
            "worker_blocked": worker_forbidden,
            "excel_working": len(excel_exports),
            "csv_working": len(csv_exports)
        }


def main():
    """Main test execution."""
    print("Starting Phase 4 Admin Dashboard MVP Backend API Tests...")
    
    runner = APITestRunner()
    runner.run_comprehensive_test()
    summary = runner.generate_summary()
    
    print(f"\n{'='*80}")
    print("✅ TESTING COMPLETE")
    print("="*80)
    
    return summary


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed with error: {str(e)}")
        sys.exit(1)