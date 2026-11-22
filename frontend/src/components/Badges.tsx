import type { Priority, Status } from "../lib/types";
import { STATUS_LABEL } from "../lib/types";

export const StatusBadge = ({ status }: { status: Status }) => (
  <span className={`badge st-${status}`}>{STATUS_LABEL[status]}</span>
);
export const PriorityBadge = ({ priority }: { priority: Priority }) => (
  <span className={`badge pr-${priority}`}>{priority}</span>
);
export const CategoryBadge = ({ category, confidence }: { category: string; confidence?: number }) => (
  <span className={`badge cat${category === "UNCLEAR" ? " cat-unclear" : ""}`}>
    {category}{confidence !== undefined && <em>{Math.round(confidence * 100)}%</em>}
  </span>
);
