def test_demo_summary_matches_approved_ot006_dataset(client):
    response = client.get("/api/v1/demo/summary")
    assert response.status_code == 200
    assert response.json() == {
        "dataset_id": "CPO-OT006-DEMO-v1",
        "chats": 33,
        "projects": 7,
        "proposals": 20,
        "safe_proposals": 16,
        "exceptions": 4,
        "acceptance_cases": 33,
        "source_files": 3,
        "originals_immutable": True,
    }
