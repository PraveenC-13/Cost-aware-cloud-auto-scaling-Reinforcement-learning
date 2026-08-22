import { useState } from "react";
import LiveMetricsChart from "../components/LiveMetricsChart";
import ForecastChart from "../components/ForecastChart";
import {
  getScalingDecision,
  type ScalingDecisionOutput,
} from "../services/api";

function Dashboard() {
  const [decision, setDecision] = useState<ScalingDecisionOutput | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleScalingDecision = async () => {
    setLoading(true);
    setError("");

    try {
      const result = await getScalingDecision({
        cpu: 68,
        memory: 60,
        predicted_cpu_next_15min: 75,
        instance_count: 4,
        current_hourly_cost: 0.2,
      });

      setDecision(result);
    } catch (err) {
      console.error(err);
      setError("Unable to connect to the auto-scaling backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <h2>Cost-Aware Cloud Auto-Scaling</h2>

      <p>
        Monitor cloud resources, cost, and auto-scaling decisions.
      </p>

      <div className="dashboard-cards">
        <div className="card">
          <h3>Current Cost</h3>
          <h2>$42.50</h2>
          <p>This month</p>
        </div>

        <div className="card">
          <h3>Active Instances</h3>
          <h2>4</h2>
          <p>Running now</p>
        </div>

        <div className="card">
          <h3>CPU Utilization</h3>
          <h2>68%</h2>
          <p>Average usage</p>
        </div>

        <div className="card">
          <h3>Auto-Scaling</h3>
          <h2>Active</h2>
          <p>Reinforcement learning</p>
        </div>
      </div>

      <div className="card">
        <h3>RL Scaling Decision</h3>

        <button onClick={handleScalingDecision} disabled={loading}>
          {loading ? "Getting Decision..." : "Get Scaling Decision"}
        </button>

        {decision && (
          <div>
            <h2>{decision.action_name}</h2>

            <p>
              Confidence: {(decision.confidence * 100).toFixed(0)}%
            </p>

            <p>{decision.reasoning}</p>
          </div>
        )}

        {error && <p>{error}</p>}
      </div>

      <LiveMetricsChart />

      <ForecastChart />
    </div>
  );
}

export default Dashboard;