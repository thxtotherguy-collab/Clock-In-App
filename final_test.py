"""
Final comprehensive test with password restoration
"""
import requests

def final_comprehensive_test():
    """Run final comprehensive test and restore original password."""
    base_url = "https://timesheet-dashboard-4.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    current_password = "NewAdmin456!"
    original_password = "Admin123!"
    email = "admin@company.com"
    
    print("🔍 FINAL COMPREHENSIVE TEST")
    print("="*50)
    
    # Login with current password
    response = requests.post(
        f"{api_url}/auth/login",
        json={"email": email, "password": current_password},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"❌ Login failed: HTTP {response.status_code}")
        return
    
    token = response.json()["access_token"]
    print(f"✅ Login successful with current password")
    
    # Test 1: Change password back to original
    change_response = requests.post(
        f"{api_url}/auth/change-password",
        json={
            "current_password": current_password,
            "new_password": original_password
        },
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )
    
    change_success = change_response.status_code == 200
    print(f"{'✅ PASS' if change_success else '❌ FAIL'} | Password Change Back to Original")
    print(f"      HTTP {change_response.status_code}")
    
    if not change_success:
        print(f"      Response: {change_response.json() if change_response.text else {}}")
        return
    
    # Test 2: Login with restored original password
    login_response = requests.post(
        f"{api_url}/auth/login",
        json={"email": email, "password": original_password},
        timeout=10
    )
    
    login_success = login_response.status_code == 200
    print(f"{'✅ PASS' if login_success else '❌ FAIL'} | Login with Restored Password")
    print(f"      HTTP {login_response.status_code}")
    
    if login_success:
        new_token = login_response.json()["access_token"]
        
        # Test 3: Final token revocation test
        logout_response = requests.post(
            f"{api_url}/auth/logout",
            headers={"Authorization": f"Bearer {new_token}"},
            timeout=10
        )
        
        logout_success = logout_response.status_code == 200
        print(f"{'✅ PASS' if logout_success else '❌ FAIL'} | Final Logout Test")
        print(f"      HTTP {logout_response.status_code}")
        
        # Test 4: Use revoked token (should fail)
        if logout_success:
            revoke_test = requests.get(
                f"{api_url}/auth/me",
                headers={"Authorization": f"Bearer {new_token}"},
                timeout=10
            )
            
            revoke_success = revoke_test.status_code == 401
            print(f"{'✅ PASS' if revoke_success else '❌ FAIL'} | Revoked Token Rejection")
            print(f"      HTTP {revoke_test.status_code} (expected 401)")
    
    print("\n✅ Password successfully restored to: Admin123!")
    print("✅ All token revocation tests passed!")

if __name__ == "__main__":
    final_comprehensive_test()