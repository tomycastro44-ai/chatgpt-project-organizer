import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

const health={status:"ok",service:"ChatGPT Project Organizer",environment:"test"};
const summary={dataset_id:"CPO",chats:33,projects:7,proposals:20,safe_proposals:16,exceptions:4,acceptance_cases:33,source_files:3,originals_immutable:true};
const capability={demo_available:true,live_available:false,default_model:"gpt-5.6",responses_api:true,structured_outputs:true};
const batch={id:"batch-1",source_kind:"approved_demo",status:"COMPLETED",created_at:"2026-07-20T20:00:00Z",completed_at:"2026-07-20T20:00:01Z",total_files:3,accepted_files:3,rejected_files:0,imported_chats:33,imported_messages:51,issue_count:0,originals_immutable:true,issues:[],source_files:[]};
const analysis={id:"analysis-1",batch_id:"batch-1",engine_version:"deterministic",status:"COMPLETED",created_at:"x",completed_at:"x",chat_count:33,finding_count:45,evidence_count:61,exact_duplicate_count:1,partial_duplicate_count:1,version_count:9,decision_count:16,task_count:11,state_signal_count:7,originals_modified:false,findings:[]};
const semantic={id:"semantic-1",analysis_run_id:"analysis-1",mode:"DEMO",model:"gpt-5.6",provider:"APPROVED_DEMO_FIXTURE",status:"COMPLETED",created_at:"x",completed_at:"x",input_digest:"b",openai_response_id:null,project_count:7,membership_count:29,exception_count:4,independent_chat_count:4,unclassified_chat_count:1,originals_modified:false,projects:[],exceptions:[],independent_chat_ids:[],unclassified_chat_ids:["CHAT-029"]};
const items=[
{id:"i1",stable_key:"P-001",operation:"CREATE_PROJECT",title:"Create detected project",reason:"Evidence-backed",confidence:"ALTA",review_required:false,status:"READY",target_ids:["PRJ-A"],candidate_project_keys:[],evidence_ids:[],payload:{},latest_review:null},
{id:"i2",stable_key:"P-018",operation:"REVIEW_MEMBERSHIP",title:"Resolve ambiguous membership",reason:"Cross-project",confidence:"MEDIA",review_required:true,status:"PENDING_REVIEW",target_ids:["CHAT-014"],candidate_project_keys:["PRJ-A","PRJ-B"],evidence_ids:[],payload:{},latest_review:null},
];
const proposals={id:"proposal-1",semantic_run_id:"semantic-1",status:"READY",created_at:"x",completed_at:null,safe_count:16,exception_count:4,safe_batch_approved:false,reviewed_exception_count:0,unresolved_exception_count:4,originals_modified:false,items};
const approved={...proposals,safe_batch_approved:true,status:"IN_REVIEW",items:[{...items[0],status:"APPROVED"},items[1]]};
const preview={proposal_run_id:"proposal-1",before_state:{semantic_run_id:"semantic-1",projects:[],exact_duplicates:[],partial_duplicates:[],independent_chat_ids:[],unclassified_chat_ids:Array.from({length:33},(_,i)=>`CHAT-${i}`),protected_chat_ids:[],originals_modified:false},proposed_state:{semantic_run_id:"semantic-1",projects:[{project_key:"PRJ-A",name:"Project A",state:"ACTIVO",current_version:"v1",previous_versions:[],discarded_versions:[],pending_tasks:[],memberships:["CHAT-001"]}],exact_duplicates:[],partial_duplicates:[],independent_chat_ids:[],unclassified_chat_ids:["CHAT-029"],protected_chat_ids:["CHAT-014"],originals_modified:false},before_hash:"a",proposed_hash:"b",approved_proposal_ids:["P-001"],unresolved_exception_ids:["P-018"],originals_modified:false};
const operation={id:"op-1",proposal_run_id:"proposal-1",status:"APPLIED",before_hash:"a",after_hash:"b",applied_proposal_ids:["P-001"],applied_at:"x",undone_at:null,state:preview.proposed_state,originals_modified:false};
const undo={id:"u1",applied_operation_id:"op-1",status:"COMPLETED",restored_hash:"a",created_at:"x",audit_history_preserved:true,originals_modified:false,state:preview.before_state};
const response=(payload:unknown)=>Promise.resolve({ok:true,json:()=>Promise.resolve(payload)});

describe("O.T. 012 workflow",()=>{
 beforeEach(()=>vi.stubGlobal("fetch",vi.fn((input:string|URL|Request,options?:RequestInit)=>{
  const url=String(input); const method=options?.method??"GET";
  if(method==="POST"&&url.endsWith("/imports/demo"))return response(batch);
  if(method==="POST"&&url.endsWith("/analysis-runs"))return response(analysis);
  if(method==="POST"&&url.endsWith("/semantic-runs"))return response(semantic);
  if(method==="POST"&&url.endsWith("/proposal-runs"))return response(proposals);
  if(method==="POST"&&url.includes("approve-safe"))return response(approved);
  if(method==="POST"&&url.endsWith("/preview"))return response(preview);
  if(method==="POST"&&url.endsWith("/apply"))return response(operation);
  if(method==="POST"&&url.endsWith("/undo"))return response(undo);
  if(method==="POST"&&url.endsWith("/review"))return response(approved);
  if(url.includes("semantic-runs/capabilities"))return response(capability);
  if(url.endsWith("/proposal-runs/proposal-1"))return response(approved);
  if(url.endsWith("/proposal-runs"))return response([]);
  if(url.endsWith("/semantic-runs"))return response([]);
  if(url.endsWith("/analysis-runs"))return response([]);
  if(url.endsWith("/imports"))return response([]);
  if(url.includes("/audit"))return response([]);
  if(url.includes("health"))return response(health); if(url.includes("demo/summary"))return response(summary);
  return response({});
 })));
 afterEach(()=>{cleanup();vi.unstubAllGlobals()});
 it("shows the final reversible workflow boundary",async()=>{render(<App/>);expect(screen.getByRole("heading",{name:/approve one coherent plan/i})).toBeInTheDocument();expect(screen.getByText("REVERSIBLE")).toBeInTheDocument();});
 it("generates and explicitly approves safe proposals",async()=>{render(<App/>);fireEvent.click(screen.getByRole("button",{name:/generate proposals/i}));await waitFor(()=>expect(screen.getByText(/approve safe proposals as one batch/i)).toBeInTheDocument());fireEvent.click(screen.getByRole("button",{name:/approve 16 safe proposals/i}));await waitFor(()=>expect(screen.getByText(/safe proposals approved/i)).toBeInTheDocument());});
 it("creates preview, applies and undoes",async()=>{render(<App/>);fireEvent.click(screen.getByRole("button",{name:/generate proposals/i}));await waitFor(()=>screen.getByRole("button",{name:/approve 16 safe proposals/i}));fireEvent.click(screen.getByRole("button",{name:/approve 16 safe proposals/i}));await waitFor(()=>screen.getByRole("button",{name:/generate preview/i}));fireEvent.click(screen.getByRole("button",{name:/generate preview/i}));await waitFor(()=>expect(screen.getByText(/1 organized projects/i)).toBeInTheDocument());fireEvent.click(screen.getByRole("button",{name:/apply simulated organization/i}));await waitFor(()=>expect(screen.getByText(/projects organized/i)).toBeInTheDocument());fireEvent.click(screen.getByRole("button",{name:/undo operation/i}));await waitFor(()=>expect(screen.getByText(/previous simulated state restored exactly/i)).toBeInTheDocument());});
 it("keeps prior workflow pages accessible",()=>{render(<App/>);fireEvent.click(screen.getByRole("button",{name:/projects & memory/i}));expect(screen.getByRole("heading",{name:/reconstruct project context/i})).toBeInTheDocument();});
});
