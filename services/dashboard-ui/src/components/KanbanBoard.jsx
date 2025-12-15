import React from 'react';
import { Briefcase, Calendar, TrendingUp } from 'lucide-react';

const KanbanColumn = ({ title, items, gradient, icon: Icon, borderColor }) => (
    <div className="bg-slate-900/50 backdrop-blur-xl rounded-2xl border border-slate-800 overflow-hidden">
        <div className={`bg-gradient-to-r ${gradient} p-4`}>
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Icon className="w-5 h-5 text-white" />
                    <h3 className="text-white font-semibold text-sm">{title}</h3>
                </div>
                <span className="bg-white/20 backdrop-blur-sm px-3 py-1 rounded-full text-xs font-bold text-white">
                    {items.length}
                </span>
            </div>
        </div>
        <div className="p-3 space-y-3 max-h-[600px] overflow-y-auto custom-scrollbar">
            {items.length === 0 ? (
                <div className="text-center py-8">
                    <Icon className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                    <p className="text-slate-500 text-xs">No applications</p>
                </div>
            ) : (
                items.map((item) => (
                    <div 
                        key={item.id} 
                        className={`bg-slate-800/50 backdrop-blur-sm p-4 rounded-xl border ${borderColor} hover:border-opacity-100 transition-all cursor-pointer group hover:shadow-lg hover:scale-[1.02]`}
                    >
                        <div className="mb-3">
                            <p className="font-semibold text-white text-sm mb-1 group-hover:text-blue-400 transition-colors">
                                {item.company || 'Unknown Company'}
                            </p>
                            <p className="text-xs text-slate-400 line-clamp-1">
                                {item.role || 'Position not specified'}
                            </p>
                        </div>
                        <div className="flex items-center justify-between pt-3 border-t border-slate-700/50">
                            <div className="flex items-center gap-1 text-slate-400">
                                <Calendar className="w-3 h-3" />
                                <span className="text-xs">
                                    {new Date(item.created_at).toLocaleDateString('en-US', { 
                                        month: 'short', 
                                        day: 'numeric' 
                                    })}
                                </span>
                            </div>
                            {item.confidence && (
                                <div className="flex items-center gap-1">
                                    <div className="w-full bg-slate-700/50 rounded-full h-1.5 w-12">
                                        <div 
                                            className={`bg-gradient-to-r ${gradient} h-1.5 rounded-full transition-all`}
                                            style={{ width: `${item.confidence * 100}%` }}
                                        ></div>
                                    </div>
                                    <span className="text-xs font-semibold text-slate-300">
                                        {(item.confidence * 100).toFixed(0)}%
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                ))
            )}
        </div>
    </div>
);

const KanbanBoard = ({ applications }) => {
    const columns = [
        { 
            title: 'Applied', 
            status: 'APPLIED', 
            gradient: 'from-blue-600 to-blue-500',
            icon: Briefcase,
            borderColor: 'border-blue-500/50'
        },
        { 
            title: 'Interviews', 
            status: 'INTERVIEW', 
            gradient: 'from-purple-600 to-purple-500',
            icon: TrendingUp,
            borderColor: 'border-purple-500/50'
        },
        { 
            title: 'Offers', 
            status: 'OFFER', 
            gradient: 'from-green-600 to-green-500',
            icon: TrendingUp,
            borderColor: 'border-green-500/50'
        },
        { 
            title: 'Rejected', 
            status: 'REJECTION', 
            gradient: 'from-red-600 to-red-500',
            icon: Briefcase,
            borderColor: 'border-red-500/50'
        },
    ];

    const getItems = (status) => {
        return applications.filter(a => a.status === status);
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {columns.map(col => (
                <KanbanColumn
                    key={col.status}
                    title={col.title}
                    gradient={col.gradient}
                    icon={col.icon}
                    borderColor={col.borderColor}
                    items={getItems(col.status)}
                />
            ))}
        </div>
    );
};

export default KanbanBoard;
