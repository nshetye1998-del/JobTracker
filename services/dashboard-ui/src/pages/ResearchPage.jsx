import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { 
  Search,
  Building2,
  Briefcase,
  MapPin,
  DollarSign,
  Users,
  Database,
  RefreshCw,
  ExternalLink,
  Filter,
  ChevronDown
} from 'lucide-react';
import ConfidenceMeter from '../components/ui/ConfidenceMeter';
import { format, parseISO } from 'date-fns';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const ResearchPage = () => {
  const [research, setResearch] = useState([]);
  const [filteredResearch, setFilteredResearch] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [dataSourceFilter, setDataSourceFilter] = useState('ALL');
  const [sortBy, setSortBy] = useState('recent');

  useEffect(() => {
    fetchResearch();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [research, searchTerm, dataSourceFilter, sortBy]);

  const fetchResearch = async () => {
    try {
      const response = await api.get('/research');
      setResearch(response.data || []);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch research:', error);
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...research];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(item =>
        item.company?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.role?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.industry?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Data source filter
    if (dataSourceFilter !== 'ALL') {
      filtered = filtered.filter(item => item.data_source === dataSourceFilter);
    }

    // Sort
    if (sortBy === 'recent') {
      filtered.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
    } else if (sortBy === 'quality') {
      filtered.sort((a, b) => (b.research_quality || 0) - (a.research_quality || 0));
    } else if (sortBy === 'company') {
      filtered.sort((a, b) => (a.company || '').localeCompare(b.company || ''));
    }

    setFilteredResearch(filtered);
  };

  const dataSources = ['ALL', ...new Set(research.map(r => r.data_source).filter(Boolean))];

  const stats = {
    total: research.length,
    avgQuality: research.length > 0
      ? (research.reduce((sum, r) => sum + (r.research_quality || 0), 0) / research.length).toFixed(1)
      : 0,
    companies: new Set(research.map(r => r.company)).size,
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-300 text-lg">Loading research...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white">Research Cache</h2>
          <p className="text-slate-400 mt-1">AI-powered company and role intelligence</p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={fetchResearch}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl border border-slate-700 transition-all"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-500/10 rounded-xl">
              <Database className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <p className="text-3xl font-bold text-white">{stats.total}</p>
              <p className="text-sm text-slate-400">Cached Entries</p>
            </div>
          </div>
        </div>

        <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-500/10 rounded-xl">
              <Search className="w-6 h-6 text-green-400" />
            </div>
            <div>
              <p className="text-3xl font-bold text-white">{stats.avgQuality}%</p>
              <p className="text-sm text-slate-400">Avg Quality Score</p>
            </div>
          </div>
        </div>

        <div className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-500/10 rounded-xl">
              <Building2 className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <p className="text-3xl font-bold text-white">{stats.companies}</p>
              <p className="text-sm text-slate-400">Unique Companies</p>
            </div>
          </div>
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
              placeholder="Search company, role, or industry..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-800/50 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
            />
          </div>

          {/* Data Source Filter */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <select
              value={dataSourceFilter}
              onChange={(e) => setDataSourceFilter(e.target.value)}
              className="w-full bg-slate-800/50 border border-slate-700 rounded-xl pl-10 pr-10 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all appearance-none"
            >
              {dataSources.map(source => (
                <option key={source} value={source}>{source}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
          </div>

          {/* Sort */}
          <div className="relative">
            <Database className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full bg-slate-800/50 border border-slate-700 rounded-xl pl-10 pr-10 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all appearance-none"
            >
              <option value="recent">Most Recent</option>
              <option value="quality">Highest Quality</option>
              <option value="company">Company (A-Z)</option>
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
          </div>
        </div>

        <div className="flex items-center gap-2 mt-4">
          <span className="text-xs text-slate-400">Showing {filteredResearch.length} of {research.length} entries</span>
        </div>
      </div>

      {/* Research Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {filteredResearch.map((item, idx) => (
          <div 
            key={idx}
            className="bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800 hover:border-blue-500/50 transition-all cursor-pointer group"
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
                  <span className="text-white font-bold text-lg">
                    {item.company?.charAt(0) || 'C'}
                  </span>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">{item.company || 'Unknown'}</h3>
                  <p className="text-sm text-slate-400">{item.role || 'Position'}</p>
                </div>
              </div>
            </div>

            {/* Quality Score */}
            <div className="mb-4">
              <ConfidenceMeter 
                confidence={item.research_quality || 0} 
                showLabel={true}
                size="sm"
              />
            </div>

            {/* Details */}
            <div className="space-y-3">
              {item.industry && (
                <div className="flex items-center gap-2 text-sm">
                  <Building2 className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-300">{item.industry}</span>
                </div>
              )}
              {item.company_size && (
                <div className="flex items-center gap-2 text-sm">
                  <Users className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-300">{item.company_size}</span>
                </div>
              )}
              {item.headquarters && (
                <div className="flex items-center gap-2 text-sm">
                  <MapPin className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-300">{item.headquarters}</span>
                </div>
              )}
              {item.salary_range && (
                <div className="flex items-center gap-2 text-sm">
                  <DollarSign className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-300">{item.salary_range}</span>
                </div>
              )}
            </div>

            {/* Description */}
            {item.description && (
              <p className="mt-4 text-sm text-slate-400 line-clamp-2">
                {item.description}
              </p>
            )}

            {/* Footer */}
            <div className="mt-4 pt-4 border-t border-slate-700 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ExternalLink className="w-3 h-3 text-slate-500" />
                <span className="text-xs text-slate-500">{item.data_source || 'Unknown'}</span>
              </div>
              {item.created_at && (
                <span className="text-xs text-slate-500">
                  {format(parseISO(item.created_at), 'MMM dd, yyyy')}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {filteredResearch.length === 0 && (
        <div className="bg-slate-900/50 backdrop-blur-xl p-12 rounded-2xl border border-slate-800 text-center">
          <Database className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400">No research data found</p>
          <p className="text-sm text-slate-500 mt-2">Research will be cached as events are processed</p>
        </div>
      )}
    </div>
  );
};

export default ResearchPage;
