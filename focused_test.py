"""
Focused test for Token Revocation and Password Change after rate limiter reset
"""
import requests
import json
import time
from datetime import datetime

def test_token_revocation_and_password_change():
    """Test JWT token revocation and password change after rate limiter reset."""
    base_url = "https://timesheet-dashboard-4.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    admin_creds = {"email": "admin@company.com", "password": "Admin123!"}
    
    print("🔍 TESTING TOKEN REVOCATION (LOGOUT) - After Backend Restart")
    print("="*60)
    
    # First, get a fresh token
    try:
        response = requests.post(f"{api_url}/auth/login", json=admin_creds, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ FAIL | Login failed: HTTP {response.status_code}")
            print(f"      Response: {response.json() if response.text else {}}")
            return
        
        token_data = response.json()
        test_token = token_data["access_token"]
        print(f"✅ PASS | Successfully obtained fresh token")
        
        # Test logout (should succeed)
        logout_response = requests.post(
            f"{api_url}/auth/logout",
            headers={"Authorization": f"Bearer {test_token}"},
            timeout=10
        )
        
        logout_success = logout_response.status_code == 200
        print(f"{'✅ PASS' if logout_success else '❌ FAIL'} | Logout Request")
        print(f"      Details: HTTP {logout_response.status_code}")
        if logout_response.text:
            print(f"      Response: {logout_response.json()}")
        
        # Now try to use the same token (should fail with 401)
        if logout_success:
            test_response = requests.get(
                f"{api_url}/auth/me",
                headers={"Authorization": f"Bearer {test_token}"},
                timeout=10
            )
            
            revoke_success = test_response.status_code == 401
            print(f"{'✅ PASS' if revoke_success else '❌ FAIL'} | Use Revoked Token (Should Fail)")
            print(f"      Details: HTTP {test_response.status_code} (expected 401)")
            if test_response.text:
                print(f"      Response: {test_response.json()}")
            
    except Exception as e:
        print(f"❌ FAIL | Token Revocation - Exception: {str(e)}")
    
    print("\n🔍 TESTING CHANGE PASSWORD - After Backend Restart")
    print("="*60)
    
    # Get a new token for password change test
    try:
        response = requests.post(f"{api_url}/auth/login", json=admin_creds, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ FAIL | Login for password change failed: HTTP {response.status_code}")
            return
        
        token_data = response.json()
        admin_token = token_data["access_token"]
        
        # Test changing password to a new valid password
        new_password = "NewAdmin456!"
        change_response = requests.post(
            f"{api_url}/auth/change-password",
            json={
                "current_password": admin_creds["password"],
                "new_password": new_password
            },
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        
        change_success = change_response.status_code == 200
        print(f"{'✅ PASS' if change_success else '❌ FAIL'} | Change Password - Valid New Password")
        print(f"      Details: HTTP {change_response.status_code}")
        if change_response.text:
            print(f"      Response: {change_response.json()}")
        
        if change_success:
            # Test login with new password
            login_response = requests.post(
                f"{api_url}/auth/login",
                json={"email": admin_creds["email"], "password": new_password},
                timeout=10
            )
            
            new_login_success = login_response.status_code == 200
            print(f"{'✅ PASS' if new_login_success else '❌ FAIL'} | Login with New Password")
            print(f"      Details: HTTP {login_response.status_code}")
            if login_response.text and not new_login_success:
                print(f"      Response: {login_response.json()}")
            
            # Change back to original password
            if new_login_success:
                new_token = login_response.json()["access_token"]
                restore_response = requests.post(
                    f"{api_url}/auth/change-password",
                    json={
                        "current_password": new_password,
                        "new_password": admin_creds["password"]
                    },
                    headers={"Authorization": f"Bearer {new_token}"},
                    timeout=10
                )
                
                restore_success = restore_response.status_code == 200
                print(f"{'✅ PASS' if restore_success else '❌ FAIL'} | Restore Original Password")
                print(f"      Details: HTTP {restore_response.status_code}")
                if restore_response.text:
                    print(f"      Response: {restore_response.json()}")
        
    except Exception as e:
        print(f"❌ FAIL | Change Password - Exception: {str(e)}")

if __name__ == "__main__":
    test_token_revocation_and_password_change()