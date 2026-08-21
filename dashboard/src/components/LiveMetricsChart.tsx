import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const data = [
  { time: "10:00", cpu: 45 },
  { time: "10:05", cpu: 52 },
  { time: "10:10", cpu: 61 },
  { time: "10:15", cpu: 68 },
  { time: "10:20", cpu: 64 },
  { time: "10:25", cpu: 72 },
];

function LiveMetricsChart() {
  return (
    <div className="chart-card">
      <h2>CPU Utilization</h2>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="cpu"
            stroke="#38bdf8"
            strokeWidth={3}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default LiveMetricsChart;