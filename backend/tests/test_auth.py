def test_login_success(client, admin_user):
    resp = client.post("/api/auth/login", json={
        "email": "admin@example.com",
        "password": "password123",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json
    assert resp.json["role"] == "admin"


def test_login_invalid_credentials(client, admin_user):
    resp = client.post("/api/auth/login", json={
        "email": "admin@example.com",
        "password": "wrong-password",
    })
    assert resp.status_code == 401


def test_admin_route_requires_admin_role(client, vendor_user):
    login = client.post("/api/auth/login", json={
        "email": "vendor@example.com",
        "password": "password123",
    })
    token = login.json["access_token"]

    resp = client.get("/api/admin/vendors", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_vendor_cannot_access_other_vendor_orders(client, vendor_user, vendor):
    login = client.post("/api/auth/login", json={
        "email": "vendor@example.com",
        "password": "password123",
    })
    token = login.json["access_token"]

    other_vendor_id = vendor.id + 999
    resp = client.get(
        f"/api/vendor/{other_vendor_id}/orders",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
