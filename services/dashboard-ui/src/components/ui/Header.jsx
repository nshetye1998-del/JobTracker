import React, { useState } from 'react';
import { Bell, Search, User, ChevronDown, Settings, LogOut } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const Header = ({ connectionStatus = 'connected' }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfile, setShowProfile] = useState(false);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/events?search=${encodeURIComponent(searchQuery)}`);
    }
  };

  return (
    <header className="sticky top-0 z-30 bg-slate-900/50 backdrop-blur-xl border-b border-slate-800">
      <div className="flex items-center justify-between gap-4 px-6 py-4">
        {/* Search Bar */}
        <div className="flex-1 max-w-md">
          <form onSubmit={handleSearch} className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search companies, roles, events..."
              className="w-full bg-slate-800/50 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </form>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-3 flex-shrink-0">
          {/* Connection Status */}
          <div className="flex items-center gap-2 bg-slate-800/50 backdrop-blur-sm px-4 py-2 rounded-full border border-slate-700">
            <div className={cn(
              "w-2 h-2 rounded-full",
              connectionStatus === 'connected' && 'bg-green-500 animate-pulse',
              connectionStatus === 'error' && 'bg-red-500',
              connectionStatus === 'connecting' && 'bg-yellow-500 animate-pulse'
            )}></div>
            <span className="text-xs font-medium text-slate-300">
              {connectionStatus === 'connected' ? 'Live' :
               connectionStatus === 'error' ? 'Offline' : 'Connecting'}
            </span>
          </div>

          {/* Notifications */}
          <div className="relative">
            <button 
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2.5 bg-slate-800/50 rounded-xl border border-slate-700 hover:bg-slate-800 transition-all"
            >
              <Bell className="w-5 h-5 text-slate-400" />
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-xs text-white flex items-center justify-center">
                3
              </span>
            </button>
            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 bg-slate-900 border border-slate-700 rounded-xl shadow-xl overflow-hidden z-50">
                <div className="p-4 border-b border-slate-800">
                  <h3 className="font-semibold text-white">Notifications</h3>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  <div className="p-4 border-b border-slate-800 hover:bg-slate-800/50 cursor-pointer">
                    <p className="text-sm text-white font-medium">New Interview Invitation</p>
                    <p className="text-xs text-slate-400 mt-1">Google - Senior Software Engineer</p>
                    <p className="text-xs text-slate-500 mt-1">2 hours ago</p>
                  </div>
                  <div className="p-4 border-b border-slate-800 hover:bg-slate-800/50 cursor-pointer">
                    <p className="text-sm text-white font-medium">Offer Received</p>
                    <p className="text-xs text-slate-400 mt-1">Meta - Staff Engineer</p>
                    <p className="text-xs text-slate-500 mt-1">1 day ago</p>
                  </div>
                  <div className="p-4 hover:bg-slate-800/50 cursor-pointer">
                    <p className="text-sm text-white font-medium">Application Update</p>
                    <p className="text-xs text-slate-400 mt-1">Stripe - Backend Engineer moved to Interview</p>
                    <p className="text-xs text-slate-500 mt-1">2 days ago</p>
                  </div>
                </div>
                <div className="p-3 border-t border-slate-800 text-center">
                  <button className="text-xs text-blue-400 hover:text-blue-300">View All Notifications</button>
                </div>
              </div>
            )}
          </div>

          {/* Authentication Section */}
          {!user ? (
            <button
              onClick={() => navigate('/login')}
              className="px-5 py-2.5 text-sm font-medium bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white rounded-xl transition-all shadow-lg hover:shadow-xl"
            >
              Sign In
            </button>
          ) : (
            <div className="relative">
              <button 
                onClick={() => setShowProfile(!showProfile)}
                className="flex items-center gap-3 p-2 bg-slate-800/50 rounded-xl border border-slate-700 hover:bg-slate-800 transition-all"
              >
                {user.picture ? (
                  <img src={user.picture} alt={user.name} className="w-8 h-8 rounded-lg" />
                ) : (
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <User className="w-5 h-5 text-white" />
                  </div>
                )}
                <div className="text-left hidden sm:block">
                  <p className="text-sm font-medium text-white">{user.name || 'User'}</p>
                  <p className="text-xs text-slate-400">{user.email}</p>
                </div>
                <ChevronDown className="w-4 h-4 text-slate-400 hidden sm:block" />
              </button>
              {showProfile && (
                <div className="absolute right-0 mt-2 w-56 bg-slate-900 border border-slate-700 rounded-xl shadow-xl overflow-hidden z-50">
                  <div className="p-4 border-b border-slate-800">
                    <p className="text-sm font-semibold text-white">{user.name}</p>
                    <p className="text-xs text-slate-400 mt-1">{user.email}</p>
                    <p className="text-xs text-slate-500 mt-1 capitalize">via {user.provider}</p>
                  </div>
                  <div className="py-2">
                    <button 
                      onClick={() => { setShowProfile(false); navigate('/settings'); }}
                      className="w-full px-4 py-2 text-left text-sm text-slate-300 hover:bg-slate-800 flex items-center gap-3"
                    >
                      <User className="w-4 h-4" />
                      My Profile
                    </button>
                    <button 
                      onClick={() => { setShowProfile(false); navigate('/settings'); }}
                      className="w-full px-4 py-2 text-left text-sm text-slate-300 hover:bg-slate-800 flex items-center gap-3"
                    >
                      <Settings className="w-4 h-4" />
                      Settings
                    </button>
                  </div>
                  <div className="border-t border-slate-800">
                    <button 
                      onClick={() => { logout(); setShowProfile(false); }}
                      className="w-full px-4 py-2 text-left text-sm text-red-400 hover:bg-slate-800 flex items-center gap-3"
                    >
                      <LogOut className="w-4 h-4" />
                      Sign Out
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
