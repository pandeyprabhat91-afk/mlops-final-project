import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL ?? "/api";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
});

export interface PredictResponse {
  prediction: "real" | "fake";
  confidence: number;
  inference_latency_ms: number;
  gradcam_image: string;
  mlflow_run_id: string;
  frames_analyzed: number;
}

export const predictVideo = async (file: File, username = "anonymous", signal?: AbortSignal): Promise<PredictResponse> => {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post<PredictResponse>("/predict", form, {
    headers: { "Content-Type": "multipart/form-data", "X-Username": username },
    signal,
  });
  return data;
};

export interface FeedbackRequest {
  request_id: string;
  predicted: "real" | "fake";
  ground_truth: "real" | "fake";
}

export const submitFeedback = async (body: FeedbackRequest): Promise<void> => {
  await apiClient.post("/feedback", body);
};

export const batchPredict = async (files: File[], username = "anonymous"): Promise<{
  results: Array<{
    filename: string;
    prediction: "real" | "fake";
    confidence: number;
    inference_latency_ms: number;
    error: string;
  }>;
  total: number;
  succeeded: number;
  failed: number;
}> => {
  const form = new FormData();
  for (const file of files) {
    form.append("files", file);
  }
  const { data } = await apiClient.post("/predict/batch", form, {
    headers: { "Content-Type": "multipart/form-data", "X-Username": username },
  });
  return data;
};

// ─── Support / Tickets ───────────────────────────────────────────────────────

export interface Ticket {
  id: string;
  username: string;
  subject: string;
  description: string;
  status: "open" | "resolved";
  resolution: string;
  created_at: string;
  resolved_at: string;
}

export const submitTicket = async (
  subject: string,
  description: string,
  username: string,
): Promise<Ticket> => {
  const { data } = await apiClient.post<Ticket>(
    "/support/tickets",
    { subject, description },
    { headers: { "X-Username": username } },
  );
  return data;
};

export const fetchTickets = async (role: string, username: string): Promise<Ticket[]> => {
  const { data } = await apiClient.get<Ticket[]>("/support/tickets", {
    headers: { "X-Role": role, "X-Username": username },
  });
  return data;
};

export const resolveTicket = async (
  ticketId: string,
  resolution: string,
  role = "admin",
): Promise<Ticket> => {
  const { data } = await apiClient.patch<Ticket>(
    `/support/tickets/${ticketId}/resolve`,
    { resolution },
    { headers: { "X-Role": role } },
  );
  return data;
};

// ─── Support Chat ────────────────────────────────────────────────────────────

export interface ChatReply {
  reply: string;
  follow_up: string | null;
  suggestions: string[] | null;
  detail: string | null;
}

export const sendChat = async (
  message: string,
  lastDetail: string | null = null,
  lastEscalate: boolean = false,
): Promise<ChatReply> => {
  const { data } = await apiClient.post<ChatReply>("/support/chat", {
    message,
    last_detail: lastDetail,
    last_escalate: lastEscalate,
  });
  return data;
};

// ─── Prediction History ──────────────────────────────────────────────────────

export interface HistoryRecord {
  id: string;
  username: string;
  filename: string;
  prediction: "real" | "fake";
  confidence: number;
  inference_latency_ms: number;
  timestamp: string;
}

export const fetchHistory = async (username: string): Promise<HistoryRecord[]> => {
  const { data } = await apiClient.get<HistoryRecord[]>("/history", {
    headers: { "X-Username": username },
  });
  return data;
};
