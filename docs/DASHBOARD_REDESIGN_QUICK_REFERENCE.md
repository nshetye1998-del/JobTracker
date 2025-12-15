# 📚 Dashboard Redesign - Quick Reference Guide

**Purpose:** Quick reference for implementing the new Job Tracker Career AI Dashboard  
**Date:** December 13, 2025

---

## 📁 Documentation Files

1. **[DATABASE_SCHEMA_DOCUMENTATION.md](./DATABASE_SCHEMA_DOCUMENTATION.md)**
   - Complete database schema for all 4 tables
   - Column definitions with data types
   - Indexes and relationships
   - JSON structure for raw_data and research_metadata
   - Sample SQL queries
   - Data visualization opportunities

2. **[API_ROUTES_SPECIFICATION.md](./API_ROUTES_SPECIFICATION.md)**
   - Complete API endpoint definitions
   - Request/response formats
   - Query parameters
   - Error handling
   - Authentication flows
   - Pagination standards

3. **[DASHBOARD_UI_DESIGN.md](./DASHBOARD_UI_DESIGN.md)**
   - UI component specifications
   - Page layouts with visual mockups
   - Color palette and design system
   - Typography and spacing
   - Chart specifications
   - Responsive design breakpoints

---

## 🚀 Quick Start Implementation

### Step 1: Review Database Schema
```bash
# File: DATABASE_SCHEMA_DOCUMENTATION.md

Key tables to understand:
- career_events (main event storage)
- research_cache (intelligent cache)
- provider_usage (analytics)
```

**Key Fields for UI:**
```javascript
// career_events table
{
  id: 1,
  event_id: "cls_19b13ecc78c161bc",
  event_type: "INTERVIEW|OFFER|APPLIED|REJECTION",
  company: "Google",
  confidence: 0.85,                          // 0-1 scale
  raw_data: {                                // JSONB
    role: "Senior Software Engineer",
    metadata: {
      method: "ai|keyword|fallback",
      provider: "groq|gemini"
    }
  },
  research_briefing: "Company research...",  // TEXT
  research_metadata: {                       // JSONB
    provider: "tavily|google|cache",
    match_type: "exact|same_company|...",
    quality: 0.95,
    cached: true
  },
  created_at: "2025-12-13T17:28:25Z"
}
```

### Step 2: Implement API Routes
```bash
# File: API_ROUTES_SPECIFICATION.md

Priority endpoints to implement first:
1. GET  /api/events                  # List events
2. GET  /api/events/:id              # Event details
3. GET  /api/events/stats            # Dashboard metrics
4. GET  /api/analytics/overview      # Overview stats
5. GET  /api/research/stats          # Cache stats
```

**Example Implementation (FastAPI):**
```python
from fastapi import FastAPI, Query
from typing import Optional

app = FastAPI()

@app.get("/api/events")
async def list_events(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    event_type: Optional[str] = None,
    company: Optional[str] = None,
    min_confidence: Optional[float] = None,
    has_research: Optional[bool] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):
    # Query database with filters
    # Apply pagination
    # Return formatted response
    pass
```

### Step 3: Build UI Components
```bash
# File: DASHBOARD_UI_DESIGN.md

Component priority order:
1. MetricCard (dashboard metrics)
2. EventCard (event list items)
3. EventTypeBadge (status badges)
4. ConfidenceMeter (confidence visualization)
5. DataTable (events table)
6. Charts (timeline, distribution)
```

**Example Component (React):**
```jsx
// components/MetricCard.jsx
export function MetricCard({ title, value, change, trend, icon: Icon, color }) {
  const colorClasses = {
    indigo: 'bg-indigo-50 text-indigo-600',
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
          {change && (
            <p className={`text-sm mt-2 ${trend === 'up' ? 'text-green-600' : 'text-gray-600'}`}>
              {trend === 'up' ? '↗' : '→'} {change}
            </p>
          )}
        </div>
        <div className={`p-3 rounded-full ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
}
```

---

## 🎨 Design System Reference

### Colors (Tailwind Classes)

**Event Types:**
```javascript
const EVENT_COLORS = {
  INTERVIEW:  'bg-blue-100 text-blue-700',    // #3B82F6
  OFFER:      'bg-green-100 text-green-700',  // #10B981
  APPLIED:    'bg-amber-100 text-amber-700',  // #F59E0B
  REJECTION:  'bg-red-100 text-red-700'       // #EF4444
};
```

**Confidence Levels:**
```javascript
const CONFIDENCE_COLORS = {
  high: 'text-green-500',    // >= 0.8
  medium: 'text-amber-500',  // 0.6 - 0.8
  low: 'text-red-500'        // < 0.6
};
```

### Icons

```javascript
const EVENT_ICONS = {
  INTERVIEW: '🎯',
  OFFER: '🎉',
  APPLIED: '📝',
  REJECTION: '❌'
};

const DATA_SOURCE_ICONS = {
  tavily: '🔬',
  google: '🔍',
  duckduckgo: '🦆',
  cache: '💾'
};
```

---

## 📊 Data Flow Diagram

```
Gmail → Ingestion → Kafka → Classifier → career_events
                                              ↓
                                    (if INTERVIEW/OFFER)
                                              ↓
                               Researcher ← research_cache
                                              ↓
                                    career_events (UPDATE)
                                              ↓
                                        Dashboard UI
```

**Data Retrieval:**
```
Dashboard → API Request → Database Query → Format Response → Render UI
```

---

## 🔍 Common Queries

### 1. Get Dashboard Overview Stats
```sql
-- Total events by type
SELECT 
  event_type,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
FROM career_events
GROUP BY event_type;

-- Average confidence
SELECT ROUND(AVG(confidence)::numeric, 2) as avg_confidence
FROM career_events;

-- Research coverage
SELECT 
  COUNT(CASE WHEN research_briefing IS NOT NULL THEN 1 END) as researched,
  COUNT(*) as total,
  ROUND(
    COUNT(CASE WHEN research_briefing IS NOT NULL THEN 1 END)::numeric / 
    COUNT(*)::numeric * 100, 
    1
  ) as coverage_percentage
FROM career_events;
```

### 2. Get Recent Events
```sql
SELECT 
  e.id,
  e.event_type,
  e.company,
  e.raw_data->>'role' as role,
  e.confidence,
  e.created_at,
  CASE WHEN e.research_briefing IS NOT NULL THEN true ELSE false END as has_research
FROM career_events e
ORDER BY e.created_at DESC
LIMIT 10;
```

### 3. Get Cache Statistics
```sql
SELECT 
  COUNT(*) as total_cached,
  COUNT(DISTINCT company_normalized) as unique_companies,
  COUNT(DISTINCT role_normalized) as unique_roles,
  ROUND(AVG(research_quality)::numeric * 100, 1) as avg_quality,
  data_source,
  COUNT(*) as count_by_source
FROM research_cache
GROUP BY data_source;
```

---

## 📱 Page Implementation Checklist

### Dashboard Home (`/dashboard`)
- [ ] Create layout with sidebar
- [ ] Implement 6 metric cards
- [ ] Add event timeline chart (Area)
- [ ] Add event distribution chart (Donut)
- [ ] Add top companies chart (Bar)
- [ ] Add recent activity feed
- [ ] Connect to `/api/analytics/overview`
- [ ] Connect to `/api/events?limit=5`

### Events List (`/events`)
- [ ] Create data table component
- [ ] Implement filter panel
- [ ] Add search functionality
- [ ] Add pagination
- [ ] Implement sort functionality
- [ ] Add event type badges
- [ ] Add confidence meters
- [ ] Connect to `/api/events`
- [ ] Add action buttons (view, edit, delete)

### Event Details (`/events/:id`)
- [ ] Create detail layout
- [ ] Display event metadata
- [ ] Display email details
- [ ] Display research briefing (expandable)
- [ ] Show research metadata (source, quality, cached)
- [ ] Add edit functionality
- [ ] Connect to `/api/events/:id`

### Research Cache (`/research`)
- [ ] Create cache statistics panel
- [ ] Add data source visualization
- [ ] Create cache table
- [ ] Implement filters (company, role, source, quality)
- [ ] Add search functionality
- [ ] Connect to `/api/research`
- [ ] Connect to `/api/research/stats`

### Analytics (`/analytics`)
- [ ] Create provider performance cards
- [ ] Add response time chart
- [ ] Add success rate chart
- [ ] Add cache performance chart
- [ ] Add quota usage visualizations
- [ ] Connect to `/api/analytics/providers`
- [ ] Connect to `/api/analytics/cache-performance`

### Timeline (`/timeline`)
- [ ] Create timeline layout
- [ ] Group events by date
- [ ] Add event cards
- [ ] Implement scroll/infinite scroll
- [ ] Add filter by date range
- [ ] Connect to `/api/events/timeline`

---

## 🛠️ Technology Stack

### Frontend
- **Framework:** React 18+
- **Styling:** Tailwind CSS
- **Charts:** Recharts
- **Icons:** Lucide React or Heroicons
- **HTTP Client:** Axios or Fetch API
- **State Management:** React Query or Zustand
- **Routing:** React Router

### Backend (Existing)
- **Framework:** FastAPI
- **Database:** PostgreSQL 13.23
- **Message Queue:** Kafka
- **Cache:** Redis

---

## 📈 Performance Optimization

### API
- Implement pagination (20-50 items per page)
- Add database indexes for common queries
- Use connection pooling
- Cache frequently accessed data (Redis)

### Frontend
- Lazy load components
- Virtual scrolling for large lists
- Debounce search inputs (300ms)
- Optimize chart rendering (max 100 data points)
- Use React.memo for expensive components

---

## 🎯 Implementation Priority

### Phase 1: Core Functionality (Week 1)
1. Dashboard overview with metrics
2. Events list with basic table
3. Event details view
4. Basic filters (event type, date range)

### Phase 2: Enhanced Features (Week 2)
1. Charts and visualizations
2. Research cache view
3. Advanced filters
4. Search functionality

### Phase 3: Analytics (Week 3)
1. Analytics dashboard
2. Provider performance tracking
3. Cache performance metrics
4. Timeline view

### Phase 4: Polish (Week 4)
1. Responsive design
2. Loading states
3. Error handling
4. Animations and transitions
5. Accessibility improvements

---

## 🐛 Testing Checklist

### Functionality
- [ ] All API endpoints return correct data
- [ ] Pagination works correctly
- [ ] Filters apply correctly
- [ ] Search returns relevant results
- [ ] Charts display accurate data
- [ ] Actions (edit, delete) work

### UI/UX
- [ ] Layout responsive on mobile/tablet/desktop
- [ ] Colors match design system
- [ ] Icons display correctly
- [ ] Loading states visible
- [ ] Error messages clear
- [ ] Tooltips helpful

### Performance
- [ ] Page load < 2 seconds
- [ ] API response < 500ms
- [ ] Charts render smoothly
- [ ] No layout shifts
- [ ] Images optimized

---

## 📞 Need Help?

**Current Data State:**
- Total Events: 11
- Event Distribution: 63.6% INTERVIEW, 27.3% OFFER, 9.1% APPLIED
- Research Cache: 3 entries (all from Tavily)
- Cache Hit Rate: 0% (just started)

**Current System Status:**
- All 16 services running ✅
- Database operational ✅
- API credentials configured ✅
- Self-learning cache active ✅

**Resources:**
- Database Schema: `docs/DATABASE_SCHEMA_DOCUMENTATION.md`
- API Routes: `docs/API_ROUTES_SPECIFICATION.md`
- UI Design: `docs/DASHBOARD_UI_DESIGN.md`
- API Health Report: `/tmp/api_status_report.md`

---

**Last Updated:** December 13, 2025  
**Ready for Implementation:** ✅ Yes

Start with Phase 1 and iterate based on user feedback!
