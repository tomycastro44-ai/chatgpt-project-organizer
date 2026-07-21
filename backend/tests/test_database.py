from sqlalchemy import inspect, text


def test_sqlite_schema_is_initialized(client):
    engine = client.app.state.database_engine
    tables = set(inspect(engine).get_table_names())
    assert tables == {
        "analysis_evidence",
        "analysis_finding_evidence",
        "analysis_findings",
        "analysis_runs",
        "chats",
        "import_batches",
        "import_issues",
        "messages",
        "project_evidence",
        "project_memberships",
        "projects",
        "schema_metadata",
        "semantic_exceptions",
        "semantic_runs",
        "source_files",
        "proposal_runs",
        "proposal_items",
        "user_reviews",
        "workspace_states",
        "applied_operations",
        "undo_operations",
        "audit_events",
    }


def test_sqlite_foreign_keys_are_enabled(client):
    engine = client.app.state.database_engine
    with engine.connect() as connection:
        enabled = connection.execute(text("PRAGMA foreign_keys")).scalar_one()
    assert enabled == 1
