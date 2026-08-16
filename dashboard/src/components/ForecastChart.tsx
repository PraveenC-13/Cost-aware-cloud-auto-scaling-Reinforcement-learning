import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const forecastData = [
  { time: "10:30", cpu: 70 },
  { time: "10:35", cpu: 73 },
  { time: "10:40", cpu: 76 },
  { time: "10:45", cpu: 80 },
  { time: "10:50", cpu: 78 },
  { time: "10:55", cpu: 74 },
];

function ForecastChart() {
  return (
    <div className="chart-card">
      <h2>CPU Forecast</h2>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={forecastData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="cpu"
            stroke="#f59e0b"
            strokeWidth={3}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default ForecastChart;