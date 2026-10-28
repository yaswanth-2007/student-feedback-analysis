def test_successful_login(client):
    """Test successful administrator authentication."""
    resp = client.post('/auth/login', data={
        'email': 'testadmin@university.edu',
        'password': 'AdminPassword123!'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Welcome back, Test Administrator!" in resp.data
    assert b"Institutional Analytics Overview" in resp.data


def test_invalid_login_credentials(client):
    """Test login rejection on incorrect password."""
    resp = client.post('/auth/login', data={
        'email': 'testadmin@university.edu',
        'password': 'WrongPassword999!'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Invalid email address or password" in resp.data


def test_unauthorized_access_protection(client):
    """Test that unauthorized users are redirected to login when accessing protected endpoints."""
    protected_urls = [
        '/admin/dashboard',
        '/admin/courses',
        '/admin/questions',
        '/admin/responses',
        '/admin/settings',
        '/admin/reports/'
    ]
    for url in protected_urls:
        resp = client.get(url, follow_redirects=False)
        assert resp.status_code in (302, 401)
        assert '/auth/login' in resp.headers.get('Location', '')


def test_logout_and_session_clearing(auth_client):
    """Test administrator sign out clears active session."""
    resp = auth_client.post('/auth/logout', follow_redirects=True)
    assert resp.status_code == 200
    assert b"You have been signed out successfully" in resp.data

    # Verify protected route is now inaccessible
    dash_resp = auth_client.get('/admin/dashboard', follow_redirects=False)
    assert dash_resp.status_code == 302
