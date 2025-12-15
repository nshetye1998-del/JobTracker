import React from 'react';
import { cn } from '../../lib/utils';

const MetricCard = ({ title, value, change, trend, icon: Icon, color = 'blue', badge }) => {
  const colorClasses = {
    blue: 'bg-blue-500/10 group-hover:bg-blue-500/20',
    purple: 'bg-purple-500/10 group-hover:bg-purple-500/20',
    green: 'bg-green-500/10 group-hover:bg-green-500/20',
    amber: 'bg-amber-500/10 group-hover:bg-amber-500/20',
    red: 'bg-red-500/10 group-hover:bg-red-500/20',
  };

  const iconColorClasses = {
    blue: 'text-blue-400',
    purple: 'text-purple-400',
    green: 'text-green-400',
    amber: 'text-amber-400',
    red: 'text-red-400',
  };

  const borderColorClasses = {
    blue: 'border-blue-500/50',
    purple: 'border-purple-500/50',
    green: 'border-green-500/50',
    amber: 'border-amber-500/50',
    red: 'border-red-500/50',
  };

  const badgeColorClasses = {
    blue: 'text-blue-400 bg-blue-500/10',
    purple: 'text-purple-400 bg-purple-500/10',
    green: 'text-green-400 bg-green-500/10',
    amber: 'text-amber-400 bg-amber-500/10',
    red: 'text-red-400 bg-red-500/10',
  };

  return (
    <div className={cn(
      "bg-slate-900/50 backdrop-blur-xl p-6 rounded-2xl border border-slate-800 transition-all group cursor-pointer hover:scale-105 hover:shadow-xl",
      `hover:${borderColorClasses[color]}`
    )}>
      <div className="flex items-center justify-between mb-4">
        <div className={cn("p-3 rounded-xl transition-all", colorClasses[color])}>
          {Icon && <Icon className={cn("w-6 h-6", iconColorClasses[color])} />}
        </div>
        {badge && (
          <span className={cn(
            "text-xs font-semibold px-3 py-1 rounded-full",
            badgeColorClasses[color]
          )}>
            {badge}
          </span>
        )}
      </div>
      <p className="text-3xl font-bold text-white mb-1">{value}</p>
      <p className="text-sm text-slate-400">{title}</p>
      {change && (
        <p className={cn(
          "text-xs mt-2 flex items-center gap-1",
          trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-red-400' : 'text-slate-400'
        )}>
          {trend === 'up' ? '↗' : trend === 'down' ? '↘' : '→'} {change}
        </p>
      )}
    </div>
  );
};

export default MetricCard;
