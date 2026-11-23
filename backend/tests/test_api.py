VALID = {"name": "Nimal", "email": "nimal@example.com", "message": "Where is my refund? It has been two weeks."}


def test_create_ticket_returns_only_id_and_message(client):
    r = client.post("/api/tickets", json=VALID)
    assert r.status_code == 201
    assert set(r.json()) == {"id", "message"}          # category/priority/draft stay internal


def test_validation_errors_are_clear_and_per_field(client):
    r = client.post("/api/tickets", json={"name": "   ", "email": "nope", "message": "hi"})
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "validation_error"
    fields = {f["field"]: f["message"] for f in err["fields"]}
    assert set(fields) == {"name", "email", "message"}
    assert "required" in fields["name"].lower()
    assert "valid email" in fields["email"].lower()
    assert "at least 10" in fields["message"]


def test_message_too_long(client):
    r = client.post("/api/tickets", json={**VALID, "message": "x" * 2001})
    assert r.status_code == 422
    assert "at most 2000" in r.json()["error"]["fields"][0]["message"]


def test_missing_fields(client):
    r = client.post("/api/tickets", json={})
    assert {f["field"] for f in r.json()["error"]["fields"]} == {"name", "email", "message"}


def test_team_endpoints_require_auth(client):
    assert client.get("/api/tickets").status_code == 401
    assert client.patch("/api/tickets/1", json={"status": "closed"}).status_code == 401


def test_login_wrong_password(client):
    r = client.post("/api/auth/login", json={"username": "agent", "password": "bad"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "invalid_credentials"


def test_list_filter_and_draft_is_stored(client, auth):
    client.post("/api/tickets", json=VALID)
    client.post("/api/tickets", json={**VALID, "message": "I need an invoice for my last purchase please"})
    rows = client.get("/api/tickets", headers=auth).json()
    assert len(rows) == 2
    refund = client.get("/api/tickets?category=refund", headers=auth).json()
    assert [t["category"] for t in refund] == ["REFUND"]
    assert refund[0]["draft_status"] in {"ready", "no_match"}      # background task already ran
    assert refund[0]["priority"] in {"low", "medium", "high"}


def test_bad_category_filter_is_400(client, auth):
    r = client.get("/api/tickets?category=DROP TABLE", headers=auth)
    assert r.status_code == 400


def test_patch_status(client, auth):
    tid = client.post("/api/tickets", json=VALID).json()["id"]
    r = client.patch(f"/api/tickets/{tid}", json={"status": "in_progress"}, headers=auth)
    assert r.status_code == 200 and r.json()["status"] == "in_progress"
    assert client.get(f"/api/tickets/{tid}", headers=auth).json()["status"] == "in_progress"


def test_patch_invalid_status_and_404(client, auth):
    tid = client.post("/api/tickets", json=VALID).json()["id"]
    assert client.patch(f"/api/tickets/{tid}", json={"status": "banana"}, headers=auth).status_code == 422
    assert client.patch("/api/tickets/9999", json={"status": "closed"}, headers=auth).status_code == 404
    assert client.get("/api/tickets/9999", headers=auth).json()["error"]["code"] == "not_found"


def test_low_confidence_becomes_unclear(client, auth):
    client.post("/api/tickets", json={**VALID, "message": "blah blah something strange happened here"})
    assert client.get("/api/tickets", headers=auth).json()[0]["category"] == "UNCLEAR"


def test_status_alias_and_plain_health(client, auth):
    tid = client.post("/api/tickets", json=VALID).json()["id"]
    r = client.patch(f"/api/tickets/{tid}/status", json={"status": "closed"}, headers=auth)
    assert r.status_code == 200 and r.json()["status"] == "closed"
    assert client.get("/health").json() == {"status": "ok"}
