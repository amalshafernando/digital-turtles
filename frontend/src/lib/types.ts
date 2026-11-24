export type Status = "open" | "in_progress" | "resolved" | "closed";
export const STATUSES: Status[] = ["open", "in_progress", "resolved", "closed"];
export const STATUS_LABEL: Record<Status, string> = {
  open: "Open", in_progress: "In progress", resolved: "Resolved", closed: "Closed",
};
export type Priority = "low" | "medium" | "high";
export type DraftStatus = "pending" | "ready" | "no_match" | "failed";

export interface DraftSource { id: string; title: string; score: number }

export interface Ticket {
  id: number;
  name: string;
  email: string;
  message: string;
  category: string;
  category_confidence: number;
  priority: Priority;
  status: Status;
  draft_status: DraftStatus;
  draft_reply: string | null;
  draft_sources: DraftSource[] | null;
  draft_flags: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface Receipt { id: number; message: string }
export interface FieldIssue { field: string; message: string }
