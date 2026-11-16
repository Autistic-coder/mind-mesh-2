export type User = { id: string; email: string; display_name: string; created_at: string };
export type MachineInput = {
  "Type": "L" | "M" | "H";
  "Air temperature [K]": number;
  "Process temperature [K]": number;
  "Rotational speed [rpm]": number;
  "Torque [Nm]": number;
  "Tool wear [min]": number;
};
export type Prediction = {
  id: string; probability: number; predicted_failure: boolean; result: string;
  risk_level: "low" | "medium" | "high"; recommendation: string;
  model_version: string; created_at: string; inputs: MachineInput;
};

