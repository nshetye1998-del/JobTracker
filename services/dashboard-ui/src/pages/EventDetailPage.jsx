import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { 
  ArrowLeft,
  Building2,
  Briefcase,
  Calendar,
  TrendingUp,
  MapPin,
  DollarSign,
  Users,
  ExternalLink,
  FileText
} from 'lucide-react';
import EventTypeBadge from '../components/ui/EventTypeBadge';
import ConfidenceMeter from '../components/ui/ConfidenceMeter';
import { format, parseISO } from 'date-fns';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const EventDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [event, setEvent] = useState(null);
  const [research, setResearch] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEventDetails();
  }, [id]);

  const fetchEventDetails = async () => {
    try {
      const eventRes = await api.get(`/applications/${id}`);
      setEvent(eventRes.data);

      // Try to fetch research data
      if (eventRes.data.company) {
        try {
          const researchRes = await api.get('/research', {
            params: { company: eventRes.data.company }
          });
          if (researchRes.data && researchRes.data.length > 0) {
            setResearch(researchRes.data[0]);
          }
        } catch (err) {
          console.log('No research data available');
        }
      }

      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch event details:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-300 text-lg">Loading event details...</p>
        </div>
      </div>
    );
  }

  if (!event) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">Event not found</p>
        <button 
          onClick={() => navigate('/events')}
          className="mt-4 text-blue-400 hover:text-blue-300"
        >
          Back to Events
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <button
        onClick={() => navigate('/events')}
        className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Events
      </button>

      {/* Header Card */}
      <div className="bg-slate-900/50 backdrop-blur-xl p-8 rounded-2xl border border-slate-800">
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center">
              <span className="text-white font-bold text-2xl">
                {event.company?.charAt(0) || 'C'}
              </span>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">{event.company || 'Unknown Company'}</h1>
              <p className="text-lg text-slate-300">{event.role || 'Software Engineer'}</p>
            </div>
          </div>
          <EventTypeBadge type={event.status} />
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center gap-3 p-4 bg-slate-800/50 rounded-xl">
            <Calendar className="w-5 h-5 text-blue-400" />
            <div>
              <p className="text-xs text-slate-400">Date</p>
              <p className="text-sm font-semibold text-white">
                {format(parseISO(event.created_at), 'MMM dd, yyyy HH:mm')}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 p-4 bg-slate-800/50 rounded-xl">
            <TrendingUp className="w-5 h-5 text-green-400" />
            <div>
              <p className="text-xs text-slate-400">Event ID</p>
              <p className="text-sm font-semibold text-white font-mono">{event.id}</p>
            </div>
          </div>

          <div className="p-4 bg-slate-800/50 rounded-xl">
            <ConfidenceMeter confidence={Math.round((event.confidence || 0.75) * 100)} />
          </div>
        </div>
      </div>

      {/* Event Summary */}
      {event.summary && (
        <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-400" />
            Event Summary
          </h2>
          <p className="text-slate-300 leading-relaxed">{event.summary}</p>
        </div>
      )}

      {/* Research Insights */}
      {research && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Company Info */}
          <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Building2 className="w-5 h-5 text-purple-400" />
              Company Information
            </h2>
            <div className="space-y-4">
              {research.industry && (
                <div>
                  <p className="text-xs text-slate-400 mb-1">Industry</p>
                  <p className="text-white">{research.industry}</p>
                </div>
              )}
              {research.company_size && (
                <div>
                  <p className="text-xs text-slate-400 mb-1">Company Size</p>
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-slate-400" />
                    <p className="text-white">{research.company_size}</p>
                  </div>
                </div>
              )}
              {research.headquarters && (
                <div>
                  <p className="text-xs text-slate-400 mb-1">Headquarters</p>
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-slate-400" />
                    <p className="text-white">{research.headquarters}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Role Info */}
          <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-green-400" />
              Role Information
            </h2>
            <div className="space-y-4">
              {research.role && (
                <div>
                  <p className="text-xs text-slate-400 mb-1">Position</p>
                  <p className="text-white">{research.role}</p>
                </div>
              )}
              {research.salary_range && (
                <div>
                  <p className="text-xs text-slate-400 mb-1">Salary Range</p>
                  <div className="flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-slate-400" />
                    <p className="text-white">{research.salary_range}</p>
                  </div>
                </div>
              )}
              {research.research_quality && (
                <div>
                  <p className="text-xs text-slate-400 mb-1">Research Quality</p>
                  <ConfidenceMeter confidence={research.research_quality} showLabel={false} />
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Research Briefing */}
      {research?.description && (
        <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800">
          <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <ExternalLink className="w-5 h-5 text-amber-400" />
            Research Briefing
          </h2>
          <p className="text-slate-300 leading-relaxed whitespace-pre-wrap">{research.description}</p>
          {research.data_source && (
            <div className="mt-4 pt-4 border-t border-slate-700">
              <p className="text-xs text-slate-400">
                Source: <span className="text-slate-300">{research.data_source}</span>
              </p>
            </div>
          )}
        </div>
      )}

      {/* Raw Data (Debug) */}
      {event.raw_data && (
        <details className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800">
          <summary className="text-lg font-bold text-white cursor-pointer hover:text-blue-400 transition-colors">
            Raw Event Data
          </summary>
          <pre className="mt-4 p-4 bg-slate-950 rounded-xl text-xs text-slate-300 overflow-x-auto">
            {JSON.stringify(event.raw_data, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
};

export default EventDetailPage;
