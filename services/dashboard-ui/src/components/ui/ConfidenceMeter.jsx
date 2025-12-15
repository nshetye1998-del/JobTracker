import React from 'react';
import { cn } from '../../lib/utils';

const ConfidenceMeter = ({ confidence, showLabel = true, size = 'md' }) => {
  const getColor = (conf) => {
    if (conf >= 85) return { bg: 'bg-green-500', text: 'text-green-400', label: 'High' };
    if (conf >= 70) return { bg: 'bg-blue-500', text: 'text-blue-400', label: 'Good' };
    if (conf >= 50) return { bg: 'bg-amber-500', text: 'text-amber-400', label: 'Medium' };
    return { bg: 'bg-red-500', text: 'text-red-400', label: 'Low' };
  };

  const sizeClasses = {
    sm: 'h-1.5',
    md: 'h-2',
    lg: 'h-3',
  };

  const color = getColor(confidence);
  const roundedConf = Math.round(confidence);

  return (
    <div className="space-y-1">
      {showLabel && (
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-400">Confidence</span>
          <span className={cn("font-semibold", color.text)}>{roundedConf}% • {color.label}</span>
        </div>
      )}
      <div className="w-full bg-slate-800 rounded-full overflow-hidden">
        <div
          className={cn("transition-all duration-500 rounded-full", color.bg, sizeClasses[size])}
          style={{ width: `${roundedConf}%` }}
        ></div>
      </div>
    </div>
  );
};

export default ConfidenceMeter;
