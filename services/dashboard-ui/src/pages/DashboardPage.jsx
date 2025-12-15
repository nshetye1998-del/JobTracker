import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { 
  TrendingUp, 
  Briefcase, 
  Award, 
  XCircle, 
  Clock,
  Building2,
  Target
} from 'lucide-react';
import { AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import MetricCard from '../components/ui/MetricCard';
import EventTypeBadge from '../components/ui/EventTypeBadge';
import ConfidenceMeter from '../components/ui/ConfidenceMeter';
import { format, parseISO } from 'date-fns';
import { useNavigate } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const DashboardPage = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({ 
    total_events: 0, 
    interviews: 0, 
    offers: 0, 
    rejections: 0,
    assessments: 0,
    applied: 0
  });
  const [events, setEvents] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, eventsRes] = await Promise.all([
        api.get('/stats'),
        api.get('/applications')
      ]);

      const statsData = statsRes.data;
      setStats({
        total_events: statsData.total_events || 0,
        interviews: statsData.interviews || 0,
        offers: statsData.offers || 0,
        rejections: statsData.rejections || 0,
        assessments: statsData.assessments || 0,
        applied: statsData.total_events - (statsData.interviews + statsData.offers + statsData.rejections) || 0
      });
      setEvents(eventsRes.data);

      // Process timeline data
      const timelineData = processTimelineData(eventsRes.data);
      setTimeline(timelineData);

      // Process company data
      const companyData = processCompanyData(eventsRes.data);
      setCompanies(companyData);

      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      setLoading(false);
    }
  };

  const processTimelineData = (events) => {
    const grouped = events.reduce((acc, event) => {
      const date = format(parseISO(event.created_at), 'MMM dd');
      if (!acc[date]) {
        acc[date] = { date, INTERVIEW: 0, OFFER: 0, APPLIED: 0, REJECTION: 0 };
      }
      acc[date][event.status] = (acc[date][event.status] || 0) + 1;
      return acc;
    }, {});

    return Object.values(grouped).sort((a, b) => new Date(a.date) - new Date(b.date));
  };

  const processCompanyData = (events) => {
    const grouped = events.reduce((acc, event) => {
      if (!acc[event.company]) {
        acc[event.company] = { company: event.company, count: 0 };
      }
      acc[event.company].count += 1;
      return acc;
    }, {});

    return Object.values(grouped)
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);
  };

  const eventDistribution = [
    { name: 'Interviews', value: stats.interviews, color: '#3B82F6' },
    { name: 'Offers', value: stats.offers, color: '#10B981' },
    { name: 'Applied', value: stats.applied, color: '#8B5CF6' },
    { name: 'Rejections', value: stats.rejections, color: '#EF4444' },
  ];

  const activeRate = stats.total_events > 0 
    ? Math.round(((stats.interviews + stats.offers) / stats.total_events) * 100) 
    : 0;

  const offerRate = stats.total_events > 0
    ? Math.round((stats.offers / stats.total_events) * 100)
    : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-300 text-lg">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div onClick={() => navigate('/events')}>
          <MetricCard
            title="Total Applications"
            value={stats.total_events}
            badge={`+${stats.total_events} total`}
            icon={TrendingUp}
            color="blue"
          />
        </div>
        <div onClick={() => navigate('/events?filter=INTERVIEW')}>
          <MetricCard
            title="Interview Invitations"
            value={stats.interviews}
            badge={`${stats.total_events > 0 ? Math.round((stats.interviews/stats.total_events)*100) : 0}%`}
            icon={Briefcase}
            color="purple"
          />
        </div>
        <div onClick={() => navigate('/events?filter=OFFER')}>
          <MetricCard
            title="Job Offers"
            value={stats.offers}
            badge={`${offerRate}%`}
            icon={Award}
            color="green"
            change={`${stats.offers} received`}
            trend="up"
          />
        </div>
        <div onClick={() => navigate('/analytics')}>
          <MetricCard
            title="Active Pipeline"
            value={`${activeRate}%`}
            badge={`${stats.interviews + stats.offers} active`}
            icon={Target}
            color="amber"
          />
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Timeline Chart */}
        <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-400" />
            Application Timeline
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={timeline}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" stroke="#94A3B8" style={{ fontSize: '12px' }} />
              <YAxis stroke="#94A3B8" style={{ fontSize: '12px' }} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1E293B', 
                  border: '1px solid #334155',
                  borderRadius: '8px'
                }}
              />
              <Legend />
              <Area type="monotone" dataKey="INTERVIEW" stackId="1" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.6} />
              <Area type="monotone" dataKey="OFFER" stackId="1" stroke="#10B981" fill="#10B981" fillOpacity={0.6} />
              <Area type="monotone" dataKey="APPLIED" stackId="1" stroke="#8B5CF6" fill="#8B5CF6" fillOpacity={0.6} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Event Distribution Pie Chart */}
        <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800">
          <h3 className="text-lg font-bold text-white mb-4">Event Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={eventDistribution}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
              >
                {eventDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1E293B', 
                  border: '1px solid #334155',
                  borderRadius: '8px'
                }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Companies Chart */}
      <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <Building2 className="w-5 h-5 text-purple-400" />
          Top Companies
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={companies}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="company" stroke="#94A3B8" style={{ fontSize: '12px' }} />
            <YAxis stroke="#94A3B8" style={{ fontSize: '12px' }} />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#1E293B', 
                border: '1px solid #334155',
                borderRadius: '8px'
              }}
            />
            <Bar dataKey="count" fill="#8B5CF6" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Recent Activity */}
      <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800">
        <h3 className="text-lg font-bold text-white mb-4">Recent Activity</h3>
        <div className="space-y-3">
          {events.slice(0, 5).map((event) => (
            <div 
              key={event.id}
              className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl border border-slate-700 hover:border-blue-500/50 transition-all cursor-pointer group"
              onClick={() => navigate(`/events/${event.id}`)}
              title="Click to view event details"
            >
              <div className="flex items-center gap-4 flex-1">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
                  <span className="text-white font-bold text-lg">
                    {event.company?.charAt(0) || 'C'}
                  </span>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="text-white font-semibold">{event.company}</h4>
                    <EventTypeBadge type={event.status} />
                  </div>
                  <p className="text-sm text-slate-400">{event.role || 'Software Engineer'}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="w-32">
                  <ConfidenceMeter confidence={Math.round((event.confidence || 0.75) * 100)} showLabel={false} />
                </div>
                <p className="text-xs text-slate-500">
                  {format(parseISO(event.created_at), 'MMM dd, HH:mm')}
                </p>
              </div>
            </div>
          ))}
          {events.length === 0 && (
            <div className="text-center py-8">
              <p className="text-slate-400">No applications yet. Start tracking your job search!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
