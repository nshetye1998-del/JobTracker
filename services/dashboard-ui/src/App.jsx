import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/ui/Sidebar';
import Header from './components/ui/Header';
import DashboardPage from './pages/DashboardPage';
import EventsPage from './pages/EventsPage';
import EventDetailPage from './pages/EventDetailPage';
import AnalyticsPage from './pages/AnalyticsPage';
import ResearchPage from './pages/ResearchPage';
import AuthCallback from './pages/AuthCallback';
import LoginPage from './pages/LoginPage';
import { AuthProvider } from './context/AuthContext';

const ORCHESTRATOR_URL = import.meta.env.VITE_ORCHESTRATOR_URL || 'http://localhost:8005';

function App() {
  const [connectionStatus, setConnectionStatus] = useState('connecting');

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
          // Keep connection alive
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

  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Auth routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/auth/callback/:provider" element={<AuthCallback />} />
          
          {/* Main app routes */}
          <Route path="/*" element={
            <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900">
              <Sidebar />
              <div className="ml-64">
                <Header connectionStatus={connectionStatus} />
                <main className="p-8">
                  <Routes>
                    <Route path="/" element={<DashboardPage />} />
                    <Route path="/events" element={<EventsPage />} />
                    <Route path="/events/:id" element={<EventDetailPage />} />
                    <Route path="/analytics" element={<AnalyticsPage />} />
                    <Route path="/research" element={<ResearchPage />} />
                    <Route path="/providers" element={<div className="text-white">Providers Page - Coming Soon</div>} />
                    <Route path="/settings" element={<div className="text-white">Settings Page - Coming Soon</div>} />
                  </Routes>
                </main>
              </div>
            </div>
          } />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
