import React, { useState } from 'react';
import { Briefcase, CheckCircle, XCircle, AlertCircle, ChevronDown, Calendar, Target } from 'lucide-react';

const EventCard = ({ event }) => {
    const [expanded, setExpanded] = useState(false);

    const getStatusConfig = (type) => {
        switch (type) {
            case 'INTERVIEW': 
                return {
                    gradient: 'from-purple-600 to-purple-500',
                    bg: 'bg-purple-500/10',
                    border: 'border-purple-500/50',
                    text: 'text-purple-400',
                    icon: Briefcase
                };
            case 'OFFER': 
                return {
                    gradient: 'from-green-600 to-green-500',
                    bg: 'bg-green-500/10',
                    border: 'border-green-500/50',
                    text: 'text-green-400',
                    icon: CheckCircle
                };
            case 'REJECTION': 
                return {
                    gradient: 'from-red-600 to-red-500',
                    bg: 'bg-red-500/10',
                    border: 'border-red-500/50',
                    text: 'text-red-400',
                    icon: XCircle
                };
            default: 
                return {
                    gradient: 'from-blue-600 to-blue-500',
                    bg: 'bg-blue-500/10',
                    border: 'border-blue-500/50',
                    text: 'text-blue-400',
                    icon: AlertCircle
                };
        }
    };

    const config = getStatusConfig(event.event_type);
    const Icon = config.icon;

    return (
        <div className={`bg-slate-900/50 backdrop-blur-xl rounded-2xl border ${config.border} hover:border-opacity-100 transition-all group overflow-hidden`}>
            {/* Header Section */}
            <div className="p-5">
                <div className="flex items-start gap-4">
                    {/* Icon */}
                    <div className={`bg-gradient-to-br ${config.gradient} p-3 rounded-xl flex-shrink-0`}>
                        <Icon className="w-6 h-6 text-white" />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-3">
                            <div className="flex-1">
                                <h3 className="text-lg font-bold text-white mb-1">
                                    {event.company || 'Unknown Company'}
                                </h3>
                                <div className="flex items-center gap-2 mb-2">
                                    <span className={`${config.bg} ${config.text} px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide`}>
                                        {event.event_type}
                                    </span>
                                    {event.confidence && (
                                        <span className="bg-slate-800/50 text-slate-300 px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1">
                                            <Target className="w-3 h-3" />
                                            {(event.confidence * 100).toFixed(0)}%
                                        </span>
                                    )}
                                </div>
                            </div>
                            
                            {/* Date */}
                            <div className="flex items-center gap-1 text-slate-400 text-xs whitespace-nowrap">
                                <Calendar className="w-3 h-3" />
                                {new Date(event.created_at).toLocaleDateString('en-US', { 
                                    month: 'short', 
                                    day: 'numeric',
                                    year: 'numeric'
                                })}
                            </div>
                        </div>

                        {/* Summary */}
                        {event.summary && (
                            <p className="text-sm text-slate-300 leading-relaxed line-clamp-2">
                                {event.summary}
                            </p>
                        )}
                    </div>
                </div>

                {/* Research Briefing Toggle */}
                {event.research_briefing && (
                    <button
                        onClick={() => setExpanded(!expanded)}
                        className="mt-4 w-full flex items-center justify-between text-sm font-semibold text-slate-400 hover:text-white transition-colors group/btn"
                    >
                        <span className="flex items-center gap-2">
                            <div className={`w-1 h-4 rounded-full bg-gradient-to-b ${config.gradient}`}></div>
                            Research Briefing
                        </span>
                        <ChevronDown className={`w-4 h-4 transition-transform ${expanded ? 'rotate-180' : ''}`} />
                    </button>
                )}
            </div>

            {/* Expanded Research Briefing */}
            {expanded && event.research_briefing && (
                <div className={`border-t ${config.border} bg-slate-800/30 p-5 animate-in slide-in-from-top duration-200`}>
                    <div className="prose prose-invert prose-sm max-w-none">
                        <p className="text-slate-300 leading-relaxed whitespace-pre-line">
                            {event.research_briefing}
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default EventCard;
