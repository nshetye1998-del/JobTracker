import React, { useState, useEffect } from 'react';
import axios from 'axios';
import EventCard from './EventCard';
import KanbanBoard from './KanbanBoard';
import ChatPanel from './ChatPanel';
import { TrendingUp, Briefcase, Award, XCircle, Activity, MessageCircle, X } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const ORCHESTRATOR_URL = import.meta.env.VITE_ORCHESTRATOR_URL || 'http://localhost:8005';

const Dashboard = () => {
    const [stats, setStats] = useState({ total_events: 0, interviews: 0, offers: 0, rejections: 0 });
    const [applications, setApplications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [connectionStatus, setConnectionStatus] = useState('connecting');
    const [isChatOpen, setIsChatOpen] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statsRes, appsRes] = await Promise.all([
                    axios.get(`${API_URL}/stats`),
                    axios.get(`${API_URL}/applications`)
                ]);
                setStats(statsRes.data);
                setApplications(appsRes.data);
            } catch (error) {
                console.error("Failed to fetch data:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    useEffect(() => {
        const eventSource = new EventSource(`${ORCHESTRATOR_URL}/events`);

        eventSource.onopen = () => {
            console.log("SSE Connected");
            setConnectionStatus('connected');
        };

        eventSource.onmessage = (event) => {
            try {
                const parsedData = JSON.parse(event.data);

                if (parsedData.type === 'heartbeat') {
                    // Optional: update last heartbeat timestamp
                } else if (parsedData.type === 'notification') {
                    const newEvent = parsedData.data;

                    // Update Stats
                    setStats(prev => {
                        const newStats = { ...prev, total_events: prev.total_events + 1 };
                        if (newEvent.event_type === 'INTERVIEW') newStats.interviews += 1;
                        else if (newEvent.event_type === 'OFFER') newStats.offers += 1;
                        else if (newEvent.event_type === 'REJECTION') newStats.rejections += 1;
                        return newStats;
                    });

                    // Update Applications List
                    setApplications(prev => {
                        const exists = prev.find(a => a.id === newEvent.event_id);
                        if (exists) {
                            return prev.map(a => a.id === newEvent.event_id ? {
                                ...a,
                                ...newEvent,
                                status: newEvent.event_type
                            } : a);
                        }
                        return [{
                            id: newEvent.event_id,
                            company: newEvent.company,
                            role: newEvent.role,
                            status: newEvent.event_type,
                            confidence: newEvent.confidence,
                            summary: newEvent.summary,
                            created_at: newEvent.classified_at || new Date().toISOString()
                        }, ...prev];
                    });
                }
            } catch (e) {
                console.error("Error parsing SSE event:", e);
            }
        };

        eventSource.onerror = (err) => {
            console.error("SSE Error:", err);
            setConnectionStatus('error');
            eventSource.close();
        };

        return () => {
            eventSource.close();
        };
    }, []);

    if (loading) return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900 flex items-center justify-center">
            <div className="text-center">
                <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-slate-300 text-lg">Loading dashboard...</p>
            </div>
        </div>
    );

    const activeRate = stats.total_events > 0 
        ? Math.round(((stats.interviews + stats.offers) / stats.total_events) * 100) 
        : 0;

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900">
            {/* Header */}
            <header className="bg-slate-900/50 backdrop-blur-xl border-b border-slate-800 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex justify-between items-center">
                        <div className="flex items-center gap-3">
                            <div className="bg-gradient-to-br from-blue-500 to-purple-600 p-2 rounded-lg">
                                <Activity className="w-6 h-6 text-white" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                                    Job Tracker Intelligence
                                </h1>
                                <p className="text-xs text-slate-400">Real-time application monitoring</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <div className="flex items-center gap-2 bg-slate-800/50 backdrop-blur-sm px-4 py-2 rounded-full border border-slate-700">
                                <div className={`w-2 h-2 rounded-full ${
                                    connectionStatus === 'connected' ? 'bg-green-500 animate-pulse' :
                                    connectionStatus === 'error' ? 'bg-red-500' : 'bg-yellow-500 animate-pulse'
                                }`}></div>
                                <span className="text-xs font-medium text-slate-300">
                                    {connectionStatus === 'connected' ? 'Live' :
                                     connectionStatus === 'error' ? 'Offline' : 'Connecting'}
                                </span>
                            </div>
                            <button
                                onClick={() => setIsChatOpen(!isChatOpen)}
                                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 p-3 rounded-full transition-all shadow-lg hover:shadow-blue-500/50"
                            >
                                {isChatOpen ? (
                                    <X className="w-5 h-5 text-white" />
                                ) : (
                                    <MessageCircle className="w-5 h-5 text-white" />
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto px-6 py-8">
                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800 hover:border-blue-500/50 transition-all group">
                        <div className="flex items-center justify-between mb-4">
                            <div className="bg-blue-500/10 p-3 rounded-xl group-hover:bg-blue-500/20 transition-all">
                                <TrendingUp className="w-6 h-6 text-blue-400" />
                            </div>
                            <span className="text-xs font-semibold text-blue-400 bg-blue-500/10 px-3 py-1 rounded-full">
                                +{stats.total_events} total
                            </span>
                        </div>
                        <p className="text-3xl font-bold text-white mb-1">{stats.total_events}</p>
                        <p className="text-sm text-slate-400">Total Applications</p>
                    </div>

                    <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800 hover:border-purple-500/50 transition-all group">
                        <div className="flex items-center justify-between mb-4">
                            <div className="bg-purple-500/10 p-3 rounded-xl group-hover:bg-purple-500/20 transition-all">
                                <Briefcase className="w-6 h-6 text-purple-400" />
                            </div>
                            <span className="text-xs font-semibold text-purple-400 bg-purple-500/10 px-3 py-1 rounded-full">
                                {stats.total_events > 0 ? Math.round((stats.interviews/stats.total_events)*100) : 0}%
                            </span>
                        </div>
                        <p className="text-3xl font-bold text-white mb-1">{stats.interviews}</p>
                        <p className="text-sm text-slate-400">Interview Invitations</p>
                    </div>

                    <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800 hover:border-green-500/50 transition-all group">
                        <div className="flex items-center justify-between mb-4">
                            <div className="bg-green-500/10 p-3 rounded-xl group-hover:bg-green-500/20 transition-all">
                                <Award className="w-6 h-6 text-green-400" />
                            </div>
                            <span className="text-xs font-semibold text-green-400 bg-green-500/10 px-3 py-1 rounded-full">
                                {stats.total_events > 0 ? Math.round((stats.offers/stats.total_events)*100) : 0}%
                            </span>
                        </div>
                        <p className="text-3xl font-bold text-white mb-1">{stats.offers}</p>
                        <p className="text-sm text-slate-400">Job Offers</p>
                    </div>

                    <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800 hover:border-red-500/50 transition-all group">
                        <div className="flex items-center justify-between mb-4">
                            <div className="bg-red-500/10 p-3 rounded-xl group-hover:bg-red-500/20 transition-all">
                                <XCircle className="w-6 h-6 text-red-400" />
                            </div>
                            <span className="text-xs font-semibold text-red-400 bg-red-500/10 px-3 py-1 rounded-full">
                                {stats.total_events > 0 ? Math.round((stats.rejections/stats.total_events)*100) : 0}%
                            </span>
                        </div>
                        <p className="text-3xl font-bold text-white mb-1">{stats.rejections}</p>
                        <p className="text-sm text-slate-400">Rejections</p>
                    </div>
                </div>

                {/* Success Rate Banner */}
                {stats.total_events > 0 && (
                    <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 backdrop-blur-xl p-6 rounded-2xl border border-blue-500/30 mb-8">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-slate-300 mb-1">Active Pipeline Rate</p>
                                <p className="text-4xl font-bold text-white">{activeRate}%</p>
                            </div>
                            <div className="text-right">
                                <p className="text-sm text-slate-400">{stats.interviews + stats.offers} active</p>
                                <p className="text-xs text-slate-500">out of {stats.total_events} total</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Kanban Board - Full Width */}
                <section className="mb-8">
                    <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                        <div className="w-1 h-6 bg-gradient-to-b from-blue-500 to-purple-600 rounded-full"></div>
                        Application Pipeline
                    </h2>
                    <KanbanBoard applications={applications} />
                </section>

                {/* Recent Activity - Full Width */}
                <section>
                    <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                        <div className="w-1 h-6 bg-gradient-to-b from-blue-500 to-purple-600 rounded-full"></div>
                        Recent Activity
                    </h2>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        {applications.slice(0, 6).map(app => (
                            <EventCard key={app.id} event={app} />
                        ))}
                        {applications.length === 0 && (
                            <div className="col-span-full bg-slate-900/50 backdrop-blur-xl p-8 rounded-2xl border border-slate-800 text-center">
                                <p className="text-slate-400">No applications yet. Start tracking your job search!</p>
                            </div>
                        )}
                    </div>
                </section>
            </div>

            {/* Floating Chat Panel */}
            {isChatOpen && (
                <div className="fixed bottom-6 right-6 w-96 z-50 animate-in slide-in-from-bottom duration-200">
                    <ChatPanel onClose={() => setIsChatOpen(false)} />
                </div>
            )}
        </div>
    );
};

export default Dashboard;
