def test_admin_login(browser: Chrome):
    """Test admin login with valid credentials"""
    # Navigate to login page
    browser.get('http://127.0.0.1:8000/login/')

    # Test valid admin credentials
    print("Testing admin credentials...")
    assert login(browser, 'legaladvisorlawe@gmail.com', 'admin@123'), "Admin login failed"