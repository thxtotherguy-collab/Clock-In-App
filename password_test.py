"""
Test with potentially changed password
"""
import requests

def test_login_with_both_passwords():
    """Test login with both possible passwords."""
    base_url = "https://timesheet-dashboard-4.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Try both possible passwords
    passwords_to_try = ["Admin123!", "NewAdmin456!"]
    email = "admin@company.com"
    
    for password in passwords_to_try:
        print(f"🔍 Trying password: {password}")
        try:
            response = requests.post(
                f"{api_url}/auth/login",
                json={"email": email, "password": password},
                timeout=10
            )
            
            print(f"   HTTP {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ SUCCESS: Login works with password: {password}")
                data = response.json()
                token = data["access_token"]
                
                # Test token revocation now
                logout_response = requests.post(
                    f"{api_url}/auth/logout",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10
                )
                
                print(f"   Logout: HTTP {logout_response.status_code}")
                if logout_response.status_code == 200:
                    # Test using revoked token
                    test_response = requests.get(
                        f"{api_url}/auth/me",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=10
                    )
                    print(f"   Using revoked token: HTTP {test_response.status_code} (expected 401)")
                    
                return password  # Return working password
            else:
                print(f"   ❌ Failed: {response.json() if response.text else 'No response'}")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
    
    return None

if __name__ == "__main__":
    working_password = test_login_with_both_passwords()