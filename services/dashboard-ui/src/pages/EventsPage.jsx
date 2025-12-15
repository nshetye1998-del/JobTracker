import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { 
  Calendar,
  Filter,
  Search,
  ChevronDown,
  Eye,
  Download,
  RefreshCw
} from 'lucide-react';
import EventTypeBadge from '../components/ui/EventTypeBadge';
import ConfidenceMeter from '../components/ui/ConfidenceMeter';
import { format, parseISO } from 'date-fns';
import { useNavigate, useLocation } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const EventsPage = () => {
  const [events, setEvents] = useState([]);
  const [filteredEvents, setFilteredEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('ALL');
  const [sortBy, setSortBy] = useState('recent');
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    fetchEvents();
  }, []);

  // Read URL query params on mount or location change
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const filter = searchParams.get('filter');
    const search = searchParams.get('search');
    if (filter && ['INTERVIEW', 'OFFER', 'APPLIED', 'REJECTION', 'ASSESSMENT'].includes(filter)) {
      setFilterType(filter);
    }
    if (search) {
      setSearchTerm(search);
    }
  }, [location.search]);

  useEffect(() => {
    applyFilters();
  }, [events, searchTerm, filterType, sortBy]);

  const fetchEvents = async () => {
    try {
      const response = await api.get('/applications');
      setEvents(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch events:', error);
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...events];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(event =>
        event.company?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        event.role?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Type filter
    if (filterType !== 'ALL') {
      filtered = filtered.filter(event => event.status === filterType);
    }

    // Sort
    if (sortBy === 'recent') {
      filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    } else if (sortBy === 'confidence') {
      filtered.sort((a, b) => (b.confidence || 0) - (a.confidence || 0));
    } else if (sortBy === 'company') {
      filtered.sort((a, b) => (a.company || '').localeCompare(b.company || ''));
    }

    setFilteredEvents(filtered);
  };

  const eventTypes = ['ALL', 'INTERVIEW', 'OFFER', 'APPLIED', 'REJECTION', 'ASSESSMENT'];

  const exportToCSV = () => {
    const headers = ['Company', 'Role', 'Status', 'Confidence', 'Created Date'];
    const csvData = filteredEvents.map(event => [
      event.company || '',
      event.role || '',
      event.status || '',
      event.confidence || '',
      format(parseISO(event.created_at), 'yyyy-MM-dd HH:mm:ss')
    ]);
    
    const csv = [headers, ...csvData]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `events_${format(new Date(), 'yyyy-MM-dd')}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-300 text-lg">Loading events...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white">Career Events</h2>
          <p className="text-slate-400 mt-1">Track and manage all your job applications</p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={fetchEvents}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl border border-slate-700 transition-all"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button 
            onClick={exportToCSV}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white rounded-xl transition-all"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              placeholder="Search company or role..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-800/50 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
            />
          </div>

          {/* Event Type Filter */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full bg-slate-800/50 border border-slate-700 rounded-xl pl-10 pr-10 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all appearance-none"
            >
              {eventTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
          </div>

          {/* Sort */}
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full bg-slate-800/50 border border-slate-700 rounded-xl pl-10 pr-10 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all appearance-none"
            >
              <option value="recent">Most Recent</option>
              <option value="confidence">Highest Confidence</option>
              <option value="company">Company (A-Z)</option>
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
          </div>
        </div>

        {/* Active Filters */}
        <div className="flex items-center gap-2 mt-4">
          <span className="text-xs text-slate-400">Showing {filteredEvents.length} of {events.length} events</span>
          {(searchTerm || filterType !== 'ALL') && (
            <button
              onClick={() => {
                setSearchTerm('');
                setFilterType('ALL');
              }}
              className="text-xs text-blue-400 hover:text-blue-300 underline"
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      {/* Events Table */}
      <div className="bg-slate-900/50 backdrop-blur-xl rounded-2xl border border-slate-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-800/50 border-b border-slate-700">
              <tr>
                <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase">Company</th>
                <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase">Role</th>
                <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase">Event Type</th>
                <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase">Confidence</th>
                <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase">Date</th>
                <th className="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filteredEvents.map((event) => (
                <tr 
                  key={event.id}
                  className="hover:bg-slate-800/30 transition-colors cursor-pointer"
                  onClick={() => navigate(`/events/${event.id}`)}
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                        <span className="text-white font-bold">
                          {event.company?.charAt(0) || 'C'}
                        </span>
                      </div>
                      <span className="text-white font-medium">{event.company || 'Unknown'}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-slate-300">
                    {event.role || 'Software Engineer'}
                  </td>
                  <td className="px-6 py-4">
                    <EventTypeBadge type={event.status} />
                  </td>
                  <td className="px-6 py-4">
                    <div className="w-40">
                      <ConfidenceMeter confidence={Math.round((event.confidence || 0.75) * 100)} size="sm" />
                    </div>
                  </td>
                  <td className="px-6 py-4 text-slate-400 text-sm">
                    {format(parseISO(event.created_at), 'MMM dd, yyyy HH:mm')}
                  </td>
                  <td className="px-6 py-4">
                    <button 
                      className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/events/${event.id}`);
                      }}
                    >
                      <Eye className="w-4 h-4 text-slate-400" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredEvents.length === 0 && (
            <div className="text-center py-12">
              <p className="text-slate-400">No events found matching your filters</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EventsPage;
