import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface MetricsSummary {
  date: string;
  campaign_id: string;
  total_impressions: number;
  total_clicks: number;
  total_conversions: number;
  total_spend: number;
  avg_ctr: number;
  avg_cpc: number;
}

interface RealtimeMetrics {
  minute: string;
  impressions: number;
  clicks: number;
  conversions: number;
  spend: number;
  avg_ctr: number;
}

function App() {
  const [summaryData, setSummaryData] = useState<MetricsSummary[]>([]);
  const [realtimeData, setRealtimeData] = useState<RealtimeMetrics[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [summaryResponse, realtimeResponse] = await Promise.all([
          axios.get(`${API_URL}/metrics/summary`),
          axios.get(`${API_URL}/metrics/realtime`)
        ]);

        setSummaryData(summaryResponse.data.data);
        setRealtimeData(realtimeResponse.data.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch data');
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute

    return () => clearInterval(interval);
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="App">
      <header className="bg-blue-600 text-white p-4">
        <h1 className="text-2xl font-bold">Ad Analytics Dashboard</h1>
      </header>

      <main className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Summary Metrics */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Campaign Performance</h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={summaryData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="total_impressions"
                  stroke="#8884d8"
                  name="Impressions"
                />
                <Line
                  type="monotone"
                  dataKey="total_clicks"
                  stroke="#82ca9d"
                  name="Clicks"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Realtime Metrics */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Realtime Performance</h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={realtimeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="minute" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="impressions"
                  stroke="#8884d8"
                  name="Impressions"
                />
                <Line
                  type="monotone"
                  dataKey="clicks"
                  stroke="#82ca9d"
                  name="Clicks"
                />
                <Line
                  type="monotone"
                  dataKey="avg_ctr"
                  stroke="#ffc658"
                  name="CTR (%)"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Metrics Summary Table */}
          <div className="col-span-1 md:col-span-2 bg-white p-4 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Campaign Metrics</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full table-auto">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="px-4 py-2">Date</th>
                    <th className="px-4 py-2">Campaign</th>
                    <th className="px-4 py-2">Impressions</th>
                    <th className="px-4 py-2">Clicks</th>
                    <th className="px-4 py-2">CTR</th>
                    <th className="px-4 py-2">CPC</th>
                    <th className="px-4 py-2">Spend</th>
                  </tr>
                </thead>
                <tbody>
                  {summaryData.map((row, index) => (
                    <tr key={index} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                      <td className="px-4 py-2">{row.date}</td>
                      <td className="px-4 py-2">{row.campaign_id}</td>
                      <td className="px-4 py-2">{row.total_impressions.toLocaleString()}</td>
                      <td className="px-4 py-2">{row.total_clicks.toLocaleString()}</td>
                      <td className="px-4 py-2">{row.avg_ctr.toFixed(2)}%</td>
                      <td className="px-4 py-2">${row.avg_cpc.toFixed(2)}</td>
                      <td className="px-4 py-2">${row.total_spend.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;