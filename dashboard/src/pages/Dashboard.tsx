import LiveMetricsChart from "../components/LiveMetricsChart";
import ForecastChart from "../components/ForecastChart";

function Dashboard() {
  return (
    <div className="dashboard">
      <h2>Cost-Aware Cloud Auto-Scaling</h2>
      <p>Monitor cloud resources, cost, and auto-scaling decisions.</p>

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

      <LiveMetricsChart />
      <ForecastChart/>
    </div>
  );
}

export default Dashboard;