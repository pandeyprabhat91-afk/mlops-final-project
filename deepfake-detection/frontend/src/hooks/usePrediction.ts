import { useState, useCallback } from "react";
import { predictVideo, type PredictResponse } from "../api/client";

type PredictionState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: PredictResponse }
  | { status: "error"; message: string };

interface UsePredictionReturn {
  state: PredictionState;
  submit: (file: File) => Promise<void>;
  reset: () => void;
}

/**
 * Custom hook that manages the full upload + inference lifecycle.
 * Wraps predictVideo() with loading, success, and error states.
 */
export function usePrediction(): UsePredictionReturn {
  const [state, setState] = useState<PredictionState>({ status: "idle" });

  const submit = useCallback(async (file: File) => {
    setState({ status: "loading" });
    try {
      const data = await predictVideo(file);
      setState({ status: "success", data });
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      const message =
        axiosErr?.response?.data?.detail ?? "An unexpected error occurred.";
      setState({ status: "error", message });
    }
  }, []);

  const reset = useCallback(() => {
    setState({ status: "idle" });
  }, []);

  return { state, submit, reset };
}
