import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { 
  BarChart3,
  TrendingUp,
  Clock,
  Zap,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { LineChart, Line, BarChart, Bar, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import MetricCard from '../components/ui/MetricCard';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const AnalyticsPage = () => {
  const [providerStats, setProviderStats] = useState([]);
  const [cacheStats, setCacheStats] = useState({
    hit_rate: 0,
    total_queries: 0,
    total_hits: 0,
    total_misses: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      // Fetch provider usage stats
      const providersRes = await api.get('/providers');
      setProviderStats(providersRes.data || []);

      // Fetch cache performance (mock for now)
      setCacheStats({
        hit_rate: 67,
        total_queries: 15,
        total_hits: 10,
        total_misses: 5
      });

      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
      setLoading(false);
    }
  };

  // Process provider data for charts
  const providerUsageData = providerStats.map(provider => ({
    name: provider.provider_name || provider.name,
    requests: provider.total_requests || 0,
    success: provider.successful_requests || 0,
    failed: provider.failed_requests || 0,
    avgResponseTime: provider.avg_response_time || 0
  }));

  const performanceData = providerStats.map(provider => ({
    name: provider.provider_name || provider.name,
    responseTime: provider.avg_response_time || 0,
    successRate: provider.total_requests > 0 
      ? ((provider.successful_requests / provider.total_requests) * 100).toFixed(1)
      : 0
  }));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-300 text-lg">Loading analytics...</p>
        </div>
      </div>
    );
  }

  const totalRequests = providerStats.reduce((sum, p) => sum + (p.total_requests || 0), 0);
  const successfulRequests = providerStats.reduce((sum, p) => sum + (p.successful_requests || 0), 0);
  const successRate = totalRequests > 0 ? ((successfulRequests / totalRequests) * 100).toFixed(1) : 0;
  const avgResponseTime = providerStats.length > 0
    ? (providerStats.reduce((sum, p) => sum + (p.avg_response_time || 0), 0) / providerStats.length).toFixed(0)
    : 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-white">Analytics Dashboard</h2>
        <p className="text-slate-400 mt-1">Monitor system performance and provider statistics</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total API Calls"
          value={totalRequests}
          badge={`${providerStats.length} providers`}
          icon={BarChart3}
          color="blue"
        />
        <MetricCard
          title="Success Rate"
          value={`${successRate}%`}
          badge={`${successfulRequests} successful`}
          icon={CheckCircle}
          color="green"
          trend="up"
        />
        <MetricCard
          title="Avg Response Time"
          value={`${avgResponseTime}ms`}
          icon={Clock}
          color="purple"
        />
        <MetricCard
          title="Cache Hit Rate"
          value={`${cacheStats.hit_rate}%`}
          badge={`${cacheStats.total_hits}/${cacheStats.total_queries}`}
          icon={Zap}
          color="amber"
          trend="up"
        />
      </div>

      {/* Provider Usage Chart */}
      <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-blue-400" />
          Provider Request Distribution
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={providerUsageData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="name" stroke="#94A3B8" style={{ fontSize: '12px' }} />
            <YAxis stroke="#94A3B8" style={{ fontSize: '12px' }} />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#1E293B', 
                border: '1px solid #334155',
                borderRadius: '8px'
              }}
            />
            <Legend />
            <Bar dataKey="success" fill="#10B981" name="Successful" radius={[8, 8, 0, 0]} />
            <Bar dataKey="failed" fill="#EF4444" name="Failed" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Performance Metrics */}
      <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 text-purple-400" />
          Response Time & Success Rate
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={performanceData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="name" stroke="#94A3B8" style={{ fontSize: '12px' }} />
            <YAxis stroke="#94A3B8" style={{ fontSize: '12px' }} />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#1E293B', 
                border: '1px solid #334155',
                borderRadius: '8px'
              }}
            />
            <Legend />
            <Line type="monotone" dataKey="responseTime" stroke="#8B5CF6" name="Avg Response (ms)" strokeWidth={2} />
            <Line type="monotone" dataKey="successRate" stroke="#10B981" name="Success Rate (%)" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Provider Details Table */}
      <div className="bg-slate-900/50 backdrop-blur-xl rounded-2xl border border-slate-800 overflow-hidden">
        <div className="p-6 border-b border-slate-800">
          <h3 className="text-lg font-bold text-white">Provider Statistics</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-800/50 border-b border-slate-700">
              <tr>
                <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase">Provider</th>
                <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase">Total Requests</th>
                <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase">Successful</th>
                <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase">Failed</th>
                <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase">Success Rate</th>
                <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase">Avg Response</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {providerStats.map((provider, idx) => {
                const successRate = provider.total_requests > 0
                  ? ((provider.successful_requests / provider.total_requests) * 100).toFixed(1)
                  : 0;
                
                return (
                  <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                          <span className="text-white font-bold text-xs">
                            {(provider.provider_name || provider.name)?.charAt(0) || 'P'}
                          </span>
                        </div>
                        <span className="text-white font-medium">{provider.provider_name || provider.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-300">{provider.total_requests || 0}</td>
                    <td className="px-6 py-4 text-green-400">{provider.successful_requests || 0}</td>
                    <td className="px-6 py-4 text-red-400">{provider.failed_requests || 0}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-24 bg-slate-800 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-full transition-all ${
                              successRate >= 90 ? 'bg-green-500' : 
                              successRate >= 70 ? 'bg-blue-500' : 
                              successRate >= 50 ? 'bg-amber-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${successRate}%` }}
                          ></div>
                        </div>
                        <span className="text-sm text-slate-300">{successRate}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-300">
                      {provider.avg_response_time ? `${provider.avg_response_time.toFixed(0)}ms` : 'N/A'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {providerStats.length === 0 && (
            <div className="text-center py-12">
              <AlertCircle className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400">No provider statistics available yet</p>
            </div>
          )}
        </div>
      </div>

      {/* Cache Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-green-500/10 rounded-xl">
              <CheckCircle className="w-6 h-6 text-green-400" />
            </div>
            <div>
              <p className="text-3xl font-bold text-white">{cacheStats.total_hits}</p>
              <p className="text-sm text-slate-400">Cache Hits</p>
            </div>
          </div>
        </div>

        <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-red-500/10 rounded-xl">
              <AlertCircle className="w-6 h-6 text-red-400" />
            </div>
            <div>
              <p className="text-3xl font-bold text-white">{cacheStats.total_misses}</p>
              <p className="text-sm text-slate-400">Cache Misses</p>
            </div>
          </div>
        </div>

        <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-blue-500/10 rounded-xl">
              <TrendingUp className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <p className="text-3xl font-bold text-white">{cacheStats.total_queries}</p>
              <p className="text-sm text-slate-400">Total Queries</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
