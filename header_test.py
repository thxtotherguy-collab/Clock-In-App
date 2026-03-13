"""
Test security headers in detail
"""
import requests

def test_security_headers():
    """Test security headers in detail."""
    base_url = "https://timesheet-dashboard-4.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    response = requests.get(f"{api_url}/health", timeout=10)
    
    print("🔍 SECURITY HEADERS ANALYSIS")
    print("="*50)
    
    security_headers = [
        "X-Frame-Options",
        "X-Content-Type-Options", 
        "X-XSS-Protection",
        "X-Request-ID",
        "X-Process-Time",
        "Cache-Control",
        "Pragma",
        "Permissions-Policy",
        "Referrer-Policy"
    ]
    
    print(f"Response Status: {response.status_code}")
    print("\nSecurity Headers Found:")
    for header in security_headers:
        if header in response.headers:
            print(f"✅ {header}: {response.headers[header]}")
        else:
            print(f"❌ {header}: MISSING")
    
    print(f"\nFull Cache-Control: '{response.headers.get('Cache-Control', 'MISSING')}'")
    print(f"Expected: 'no-store, no-cache, must-revalidate, private'")
    
    # Check if it's a cloudflare override
    print(f"\nCloudflare Headers:")
    cf_headers = [h for h in response.headers.keys() if h.lower().startswith('cf-')]
    for header in cf_headers:
        print(f"  {header}: {response.headers[header]}")

if __name__ == "__main__":
    test_security_headers()