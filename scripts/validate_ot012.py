from __future__ import annotations
import csv, hashlib, json, os, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))

def main():
 required=['backend/app/services/proposal_service.py','backend/app/api/routes/proposals.py','frontend/src/pages/ProposalsPage.tsx','docs/OT-012_PROPOSALS_APPLY_UNDO.md','tests/matrices/ot012_acceptance_matrix.csv']
 for item in required: assert (ROOT/item).is_file(),item
 with (ROOT/'tests/matrices/ot012_acceptance_matrix.csv').open(encoding='utf-8') as h: rows=list(csv.DictReader(h))
 assert len(rows)==68 and len({r['case_id'] for r in rows})==68
 manifest=json.loads((ROOT/'demo-data/IMMUTABILITY_MANIFEST.json').read_text(encoding='utf-8'))
 for item in manifest['files']:
  path=ROOT/item['path']; assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
 frontend=(ROOT/'frontend/src').read_text(encoding='utf-8') if False else ''
 assert 'OPENAI_API_KEY' not in ''.join(p.read_text(encoding='utf-8') for p in (ROOT/'frontend/src').rglob('*') if p.is_file())
 with tempfile.TemporaryDirectory() as td:
  os.environ['DATABASE_URL']=f"sqlite:///{Path(td)/'validate.db'}";os.environ['IMPORTS_DIR']=str(Path(td)/'imports');os.environ['DEMO_DATA_DIR']=str(ROOT/'demo-data/canonical');os.environ['DEMO_SOURCE_DIR']=str(ROOT/'demo-data/source');os.environ.pop('OPENAI_API_KEY',None)
  from app.core.config import get_settings
  get_settings.cache_clear()
  from app.main import create_app
  from fastapi.testclient import TestClient
  with TestClient(create_app()) as c:
   batch=c.post('/api/v1/imports/demo').json();analysis=c.post('/api/v1/analysis-runs',json={'batch_id':batch['id']}).json();semantic=c.post('/api/v1/semantic-runs',json={'analysis_run_id':analysis['id'],'mode':'DEMO'}).json();run=c.post('/api/v1/proposal-runs',json={'semantic_run_id':semantic['id']}).json()
   assert len(run['items'])==20 and run['safe_count']==16 and run['exception_count']==4
   run=c.post(f"/api/v1/proposal-runs/{run['id']}/approve-safe").json()
   decisions={'P-017':('REJECT',{}),'P-018':('CORRECT',{'project_key':'PRJ-SCANLINK'}),'P-019':('REJECT',{}),'P-020':('APPROVE',{})}
   for item in run['items']:
    if item['stable_key'] in decisions:
     decision,correction=decisions[item['stable_key']];run=c.post(f"/api/v1/proposal-runs/{run['id']}/items/{item['id']}/review",json={'decision':decision,'correction':correction}).json()
   preview=c.post(f"/api/v1/proposal-runs/{run['id']}/preview").json();assert len(preview['proposed_state']['projects'])==7;assert preview['unresolved_exception_ids']==[]
   applied=c.post(f"/api/v1/proposal-runs/{run['id']}/apply").json();assert applied['after_hash']==preview['proposed_hash'] and applied['originals_modified'] is False
   undone=c.post(f"/api/v1/applied-operations/{applied['id']}/undo").json();assert undone['restored_hash']==applied['before_hash'] and undone['audit_history_preserved'] is True
   audit=c.get(f"/api/v1/proposal-runs/{run['id']}/audit").json();assert len(audit)==9 and [e['sequence'] for e in audit]==list(range(1,10))
  get_settings.cache_clear()
 print('OT-012 VALIDATION: OK');print('Proposals: 20');print('Safe proposals: 16');print('Exceptions: 4');print('Projects after preview: 7');print('Audit events: 9');print('Undo exact restore: OK');print('Acceptance cases: 68');print('Original integrity: OK')
if __name__=='__main__':main()
