export interface User {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
  is_active: boolean;
  last_login_at: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface DashboardMetrics {
  total_institutions: number;
  active_approvals: number;
  student_records: number;
  pending_submissions: number;
  validation_issues: number;
  open_cases: number;
}

export interface DashboardData {
  demo_mode: boolean;
  demo_label: string | null;
  metrics: DashboardMetrics;
  cases_by_risk: { low: number; medium: number; high: number; critical: number };
  recent_audit_activity: AuditEntry[];
  submission_trends: SubmissionTrend[];
  intake_reconciliation: IntakeRecon[];
  alerts: Alert[];
}

export interface AuditEntry {
  id: string;
  action: string;
  actor_role: string | null;
  entity_type: string | null;
  outcome: string;
  created_at: string | null;
}

export interface SubmissionTrend {
  id: string;
  version: number;
  status: string;
  total_rows: number;
  created_at: string | null;
}

export interface IntakeRecon {
  institution_id: string;
  institution_name: string;
  course_id: string;
  course_name: string;
  approved_intake: number;
  actual_enrolment: number;
  variance: number;
  status: string;
}

export interface Alert {
  type: string;
  severity: string;
  message: string;
  institution_id?: string;
  course_id?: string;
  approved?: number;
  actual?: number;
  case_id?: string;
  case_number?: string;
}

export interface Institution {
  id: string;
  code: string;
  name: string;
  institution_type: string;
  location?: string;
  state?: string;
  city?: string;
  is_synthetic: boolean;
  submission_count: number;
  student_count: number;
  open_issues: number;
  approvals: InstitutionApproval[];
}

export interface InstitutionApproval {
  id: string;
  academic_year_id: string;
  approval_status: string;
  approval_date: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface StudentRecord {
  id: string;
  apaar_reference_masked: string;
  student_name: string;
  institution_id: string;
  institution_name: string;
  course_id: string;
  course_name: string;
  academic_year_id: string;
  admission_status: string;
  enrolment_status: string;
  verification_status: string;
  is_synthetic: boolean;
  created_at: string;
}

export interface RiskCase {
  id: string;
  case_number: string;
  title: string;
  entity_type: string;
  entity_ref: string;
  risk_score: number;
  risk_band: string;
  status: string;
  severity: string;
  institution_id?: string;
  risk_version: string;
  created_at: string;
}

export interface ValidationIssue {
  id: string;
  issue_code: string;
  severity: string;
  field_name: string | null;
  row_number: number | null;
  explanation: string;
  expected_value: string | null;
  observed_value: string | null;
  recommended_action: string | null;
  status: string;
  resolved_at: string | null;
  resolution_note: string | null;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  ref_id: string | null;
  ref_type: string | null;
  created_at: string;
}

export interface CopilotResponse {
  question: string;
  answer: string;
  evidence_refs: any[];
  provider: string;
  is_llm: boolean;
  is_synthetic: boolean;
  demo_label: string | null;
}

export const ROLE_LABELS: Record<string, string> = {
  SUPER_ADMIN: "Super Admin",
  AICTE_ADMIN: "AICTE Admin",
  INSTITUTION_ADMIN: "Institution Admin",
  FRAUD_ANALYST: "Fraud Analyst",
  AUDITOR: "Auditor",
};

export const RISK_BAND_COLORS: Record<string, string> = {
  low: "text-green-600 bg-green-50 border-green-200",
  medium: "text-yellow-600 bg-yellow-50 border-yellow-200",
  high: "text-orange-600 bg-orange-50 border-orange-200",
  critical: "text-red-600 bg-red-50 border-red-200",
};

export const STATUS_COLORS: Record<string, string> = {
  open: "text-blue-600 bg-blue-50",
  resolved: "text-green-600 bg-green-50",
  closed: "text-gray-600 bg-gray-50",
  assigned: "text-purple-600 bg-purple-50",
  under_review: "text-yellow-600 bg-yellow-50",
  awaiting_institution_response: "text-orange-600 bg-orange-50",
};
