import type { Analysis, Borrower, Covenant, DealComparison, DebtStructure, GuidedDemo, Loan, PrivateAnalysis, SavedRecord, SavedSummary, Sensitivity, SourcesUses } from "./types";

const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
export const API_URL = (configuredApiUrl || (process.env.NODE_ENV === "production" ? "" : "http://localhost:8000")).replace(/\/$/, "");

async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Unexpected server response" }));
    const detail = Array.isArray(body.detail) ? body.detail.map((x: { msg: string }) => x.msg).join(", ") : body.detail;
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.json();
}
export const getBorrowers = () => fetch(`${API_URL}/borrowers`, { cache: "no-store" }).then(parse<Borrower[]>);
export const getBorrower = (id: string) => fetch(`${API_URL}/borrowers/${id}`, { cache: "no-store" }).then(parse<Borrower>);
export const analyzeLoan = (borrower_id: string, loan: Loan, covenants: Covenant[], scenario_ids: string[]) => fetch(`${API_URL}/loans/analyze`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ borrower_id, loan, covenants, scenario_ids }) }).then(parse<Analysis>);
export const generateMemo = (borrower_id: string, loan: Loan, covenants: Covenant[], scenario_ids: string[]) => fetch(`${API_URL}/credit-memo/generate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ borrower_id, loan, covenants, scenario_ids, analyst_name: "CovenantIQ Credit Desk" }) }).then(parse<{ html: string }>);

const privateBody = (borrower_id:string, debt_structure:DebtStructure, covenants:Covenant[], scenario_ids:string[], sources_uses:SourcesUses) => ({ borrower_id, debt_structure, covenants, scenario_ids, sources_uses });
export const analyzePrivateCredit = (borrower_id:string, debt_structure:DebtStructure, covenants:Covenant[], scenario_ids:string[], sources_uses:SourcesUses) => fetch(`${API_URL}/private-credit/analyze`, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(privateBody(borrower_id,debt_structure,covenants,scenario_ids,sources_uses))}).then(parse<PrivateAnalysis>);
export const runSensitivity = (borrower_id:string, debt_structure:DebtStructure, covenants:Covenant[]) => fetch(`${API_URL}/sensitivity/run`, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({borrower_id,debt_structure,covenants})}).then(parse<Sensitivity>);
export const generatePrivateMemo = (borrower_id:string, debt_structure:DebtStructure, covenants:Covenant[], scenario_ids:string[], sources_uses:SourcesUses) => fetch(`${API_URL}/credit-memo/generate-v2`, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({...privateBody(borrower_id,debt_structure,covenants,scenario_ids,sources_uses),analyst_name:"CovenantIQ Private Credit"})}).then(parse<{html:string}>);
export const saveAnalysis = (analysis_name:string, borrower_id:string, debt_structure:DebtStructure, covenants:Covenant[], scenario_ids:string[], sources_uses:SourcesUses) => fetch(`${API_URL}/analyses`, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({analysis_name,...privateBody(borrower_id,debt_structure,covenants,scenario_ids,sources_uses)})}).then(parse<SavedRecord>);
export const listAnalyses = () => fetch(`${API_URL}/analyses`,{cache:"no-store"}).then(parse<SavedSummary[]>);
export const getAnalysis = (id:string) => fetch(`${API_URL}/analyses/${id}`,{cache:"no-store"}).then(parse<SavedRecord>);
export const deleteAnalysis = async (id:string) => { const response=await fetch(`${API_URL}/analyses/${id}`,{method:"DELETE"}); if(!response.ok) throw new Error(`Delete failed (${response.status})`); };
export const compareAnalyses = (analysis_ids:string[]) => fetch(`${API_URL}/analyses/compare`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({analysis_ids})}).then(parse<DealComparison>);
export const getGuidedDemos = () => fetch(`${API_URL}/guided-demos`,{cache:"no-store"}).then(parse<GuidedDemo[]>);
