import axios from "axios";

const api = axios.create({
  baseURL: "/api",
});

export interface ScalingStateInput {
  cpu: number;
  memory: number;
  predicted_cpu_next_15min: number;
  instance_count: number;
  current_hourly_cost: number;
}

export interface ScalingDecisionOutput {
  action: number;
  action_name: string;
  confidence: number;
  reasoning: string;
}

export async function getScalingDecision(
  state: ScalingStateInput
): Promise<ScalingDecisionOutput> {
  const response = await api.post<ScalingDecisionOutput>("/decide", state);

  return response.data;
}