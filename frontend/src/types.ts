export type Role = "ADMINISTRATOR" | "MANAGER" | "EMPLOYEE" | "AUDITOR";

export interface User {
  id: number;
  email: string;
  name: string;
  role: Role;
  department: string;
  clearance_level: string;
  account_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Tokens { access: string; refresh: string }

export interface Document {
  id: string;
  title: string;
  description: string;
  document_type: string;
  classification: string;
  owner: { id: number; name: string; department: string };
  original_filename: string;
  file_size: number;
  content_type: string;
  created_at: string;
  updated_at: string;
  updated_by: { id: number; name: string } | null;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  user: number | null;
  event_type: string;
  outcome: "SUCCESS" | "FAILURE" | "DENIED";
  resource_type: string;
  resource_id: string;
  source_ip: string | null;
  user_agent: string;
  metadata: Record<string, unknown>;
  previous_hash: string;
  current_hash: string;
}

export interface ChainStatus { valid: boolean; checked: number; error?: string }

export interface AnomalyStatus {
  model_version: string;
  feature_schema_version: string;
  feature_names: string[];
  minimum_profiles: number;
  loaded: boolean;
}

export interface AnomalyResult {
  id: number;
  subject: Pick<User, "id" | "email" | "name">;
  window_start: string;
  window_end: string;
  anomaly_score: number;
  classification: "NORMAL" | "ANOMALOUS";
  model_version: string;
  feature_schema_version: string;
  feature_summary: Record<string, number>;
  detected_at: string;
  reviewed: boolean;
}
