import React from 'react';
import { cn } from '../../lib/utils';

const EventTypeBadge = ({ type }) => {
  const badgeStyles = {
    INTERVIEW: {
      bg: 'bg-blue-500/10',
      text: 'text-blue-400',
      border: 'border-blue-500/30',
      label: 'Interview',
    },
    OFFER: {
      bg: 'bg-green-500/10',
      text: 'text-green-400',
      border: 'border-green-500/30',
      label: 'Offer',
    },
    APPLIED: {
      bg: 'bg-purple-500/10',
      text: 'text-purple-400',
      border: 'border-purple-500/30',
      label: 'Applied',
    },
    REJECTION: {
      bg: 'bg-red-500/10',
      text: 'text-red-400',
      border: 'border-red-500/30',
      label: 'Rejected',
    },
    ASSESSMENT: {
      bg: 'bg-amber-500/10',
      text: 'text-amber-400',
      border: 'border-amber-500/30',
      label: 'Assessment',
    },
  };

  const style = badgeStyles[type] || badgeStyles.APPLIED;

  return (
    <span className={cn(
      "inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border",
      style.bg,
      style.text,
      style.border
    )}>
      {style.label}
    </span>
  );
};

export default EventTypeBadge;
