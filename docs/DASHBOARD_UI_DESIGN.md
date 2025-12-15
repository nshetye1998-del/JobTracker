# 🎨 Job Tracker Career AI - Dashboard UI/UX Design Specification

**Version:** 1.0  
**Date:** December 13, 2025  
**Framework:** React + Tailwind CSS  
**UI Port:** 3300

---

## 📑 Table of Contents

1. [Design System](#design-system)
2. [Page Layouts](#page-layouts)
3. [Component Specifications](#component-specifications)
4. [Color Coding & Icons](#color-coding--icons)
5. [Data Visualization](#data-visualization)
6. [Responsive Design](#responsive-design)
7. [User Flows](#user-flows)

---

## Design System

### Color Palette

**Event Type Colors:**
```css
INTERVIEW:  #3B82F6 (Blue-500)    /* Target icon 🎯 */
OFFER:      #10B981 (Green-500)   /* Party icon 🎉 */
APPLIED:    #F59E0B (Amber-500)   /* Document icon 📝 */
REJECTION:  #EF4444 (Red-500)     /* Cross icon ❌ */
```

**UI Colors:**
```css
Primary:    #6366F1 (Indigo-500)
Secondary:  #8B5CF6 (Violet-500)
Success:    #10B981 (Green-500)
Warning:    #F59E0B (Amber-500)
Error:      #EF4444 (Red-500)
Info:       #3B82F6 (Blue-500)

Background: #F9FAFB (Gray-50)
Surface:    #FFFFFF (White)
Border:     #E5E7EB (Gray-200)
Text:       #111827 (Gray-900)
TextMuted:  #6B7280 (Gray-500)
```

**Confidence Levels:**
```css
High (0.8-1.0):   #10B981 (Green-500)   /* ●●●●● */
Medium (0.6-0.8): #F59E0B (Amber-500)   /* ●●●○○ */
Low (0.0-0.6):    #EF4444 (Red-500)     /* ●○○○○ */
```

### Typography

```css
Headings:
  H1: text-4xl font-bold (36px)
  H2: text-3xl font-bold (30px)
  H3: text-2xl font-semibold (24px)
  H4: text-xl font-semibold (20px)
  H5: text-lg font-medium (18px)

Body:
  Large: text-base (16px)
  Normal: text-sm (14px)
  Small: text-xs (12px)

Font Family: Inter, system-ui, sans-serif
```

### Spacing

```css
xs:  4px   (0.25rem)
sm:  8px   (0.5rem)
md:  16px  (1rem)
lg:  24px  (1.5rem)
xl:  32px  (2rem)
2xl: 48px  (3rem)
```

### Shadows

```css
sm:  0 1px 2px 0 rgb(0 0 0 / 0.05)
md:  0 4px 6px -1px rgb(0 0 0 / 0.1)
lg:  0 10px 15px -3px rgb(0 0 0 / 0.1)
xl:  0 20px 25px -5px rgb(0 0 0 / 0.1)
```

### Border Radius

```css
sm:  4px
md:  8px
lg:  12px
xl:  16px
full: 9999px
```

---

## Page Layouts

### 1. Dashboard Home (`/dashboard`)

**Layout Structure:**
```
┌─────────────────────────────────────────────────────────────┐
│  ☰ Sidebar (240px)  │  Main Content (flex-1)               │
│                     │                                       │
│  📊 Dashboard       │  ┌───────────────────────────────┐   │
│  📋 Events          │  │  Header: "Dashboard Overview" │   │
│  🔬 Research Cache  │  └───────────────────────────────┘   │
│  📈 Analytics       │                                       │
│  ⚙️  Settings       │  ┌─────────┐ ┌─────────┐ ┌──────┐  │
│                     │  │Metric 1 │ │Metric 2 │ │Metric3│  │
│  ───────────────    │  └─────────┘ └─────────┘ └──────┘  │
│                     │                                       │
│  👤 User Profile    │  ┌───────────────────────────────┐   │
│  🔔 Notifications   │  │  Charts & Visualizations      │   │
│                     │  └───────────────────────────────┘   │
│                     │                                       │
│                     │  ┌───────────────────────────────┐   │
│                     │  │  Recent Activity Feed         │   │
│                     │  └───────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Key Metrics Grid (Top Section):**
```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  <MetricCard
    title="Total Applications"
    value={11}
    change="+11 from last week"
    trend="up"
    icon={FileTextIcon}
    color="indigo"
  />
  <MetricCard
    title="This Week"
    value={11}
    change="+11 from last week"
    trend="up"
    icon={CalendarIcon}
    color="blue"
  />
  <MetricCard
    title="Success Rate"
    value="27.3%"
    subtitle="3 offers / 11 applications"
    icon={TrophyIcon}
    color="green"
  />
  <MetricCard
    title="Interviews"
    value={7}
    percentage="63.6% of total"
    icon={TargetIcon}
    color="blue"
  />
  <MetricCard
    title="Offers"
    value={3}
    percentage="27.3% of total"
    icon={PartyPopperIcon}
    color="green"
  />
  <MetricCard
    title="Cache Hit Rate"
    value="0%"
    subtitle="Just started - building..."
    icon={DatabaseIcon}
    color="violet"
  />
</div>
```

**Charts Section:**
```jsx
<div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
  <Card title="Event Timeline" subtitle="Last 30 days">
    <AreaChart data={timelineData} />
  </Card>
  
  <Card title="Event Distribution" subtitle="By type">
    <DonutChart data={distributionData} />
  </Card>
  
  <Card title="Top Companies" subtitle="Most applications">
    <BarChart data={companiesData} />
  </Card>
  
  <Card title="Confidence Distribution" subtitle="Classification accuracy">
    <ProgressBars data={confidenceData} />
  </Card>
</div>
```

**Recent Activity Feed:**
```jsx
<Card title="Recent Events" action="View All" className="mt-8">
  <EventList events={recentEvents} limit={5} compact />
</Card>
```

### 2. Events List (`/events`)

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Header: "Career Events"                                    │
│  ┌─────────────────┐ ┌──────────┐ ┌─────────────────────┐ │
│  │ 🔍 Search...    │ │ Filters ▼│ │ + New Event         │ │
│  └─────────────────┘ └──────────┘ └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Active Filters:                                            │
│  [INTERVIEW ×] [Min Confidence: 0.7 ×] [Has Research ×]    │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Status │ Company │ Role │ Confidence │ Date │ Actions │ │
│  ├───────────────────────────────────────────────────────┤ │
│  │ 🎯    │ Google  │ SWE  │ ●●●●○ 85%│ 2h  │ 👁️ ✏️ 🗑️ │ │
│  │ 🎉    │ MSFT    │ Staff│ ●●●●● 98%│ 5h  │ 👁️ ✏️ 🗑️ │ │
│  │ 📝    │ Amazon  │ Prin.│ ●●●○○ 75%│ 8h  │ 👁️ ✏️ 🗑️ │ │
│  └───────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Showing 1-20 of 11 results    ◀ 1 2 3 ▶                  │
└─────────────────────────────────────────────────────────────┘
```

**Filter Panel (Expandable Sidebar):**
```jsx
<FilterPanel>
  <FilterSection title="Event Type">
    <Checkbox label="Interview" count={7} checked />
    <Checkbox label="Offer" count={3} />
    <Checkbox label="Applied" count={1} />
    <Checkbox label="Rejection" count={0} disabled />
  </FilterSection>
  
  <FilterSection title="Date Range">
    <DateRangePicker />
  </FilterSection>
  
  <FilterSection title="Confidence">
    <RangeSlider min={0} max={1} step={0.1} />
  </FilterSection>
  
  <FilterSection title="Company">
    <Autocomplete options={companies} />
  </FilterSection>
  
  <FilterSection title="Research">
    <Checkbox label="Has research" />
    <Checkbox label="Cached research" />
  </FilterSection>
  
  <Button variant="secondary" fullWidth>Clear Filters</Button>
</FilterPanel>
```

**Table Actions:**
- **View (👁️)**: Open event details modal
- **Edit (✏️)**: Edit event inline or in modal
- **Delete (🗑️)**: Delete with confirmation dialog

### 3. Event Details (`/events/:id`)

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  ← Back to Events                              [Edit] [×]   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │  🎯 INTERVIEW                                        │  │
│  │  Google - Senior Software Engineer                  │  │
│  │  Confidence: ●●●●○ 85%                              │  │
│  │  Classified: AI (Groq) • 2 hours ago                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  📧 Email Details                                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Message ID: 19b13ecc78c161bc                         │  │
│  │ Received: Dec 13, 2025 5:28 PM                       │  │
│  │                                                       │  │
│  │ "Dear Nikunj, Thank you for your interest in the     │  │
│  │  Senior Software Engineer position at Google..."     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  🔬 Company Research                    [Refresh Research] │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Source: 🟢 Tavily • Quality: ●●●●● 95%             │  │
│  │ Response Time: 450ms • Cached: ✅ Yes                │  │
│  │                                                       │  │
│  │ Google LLC is an American multinational technology   │  │
│  │ company focusing on search engine technology,        │  │
│  │ online advertising, cloud computing...               │  │
│  │                                                       │  │
│  │ [Read More ▼]                                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  📊 Metadata                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Event ID: cls_19b13ecc78c161bc                       │  │
│  │ Classification Method: AI                            │  │
│  │ Provider: Groq (llama-3.1-8b-instant)               │  │
│  │ Created: 2025-12-13 17:28:25 UTC                    │  │
│  │ Updated: 2025-12-13 17:30:00 UTC                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 4. Research Cache (`/research`)

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Header: "Research Cache"                                   │
│  ┌─────────────────┐ ┌──────────┐ ┌─────────────────────┐ │
│  │ 🔍 Search...    │ │ Filters ▼│ │ + Add Research      │ │
│  └─────────────────┘ └──────────┘ └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  📊 Cache Statistics                                        │
│  ┌──────────┐ ┌─────────────┐ ┌──────────────┐ ┌────────┐│
│  │ Total: 3 │ │Companies: 3 │ │ Roles: 3     │ │Hit: 0% ││
│  └──────────┘ └─────────────┘ └──────────────┘ └────────┘│
│                                                             │
│  Data Sources:                                              │
│  Tavily: ███████████████ 100% (3)                         │
│  Google: ░░░░░░░░░░░░░░░ 0% (0)                           │
│  DuckDuckGo: ░░░░░░░░░░░ 0% (0)                           │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────┐ │
│  │Company │ Role │ Quality │ Source │ Cached │ Actions  │ │
│  ├───────────────────────────────────────────────────────┤ │
│  │Google  │ SWE  │●●●●● 95%│Tavily │ 2h ago │ 👁️ ✏️ 🗑️│ │
│  │MSFT    │Staff │●●●●● 95%│Tavily │ 5h ago │ 👁️ ✏️ 🗑️│ │
│  │Amazon  │Prin. │●●●●● 95%│Tavily │ 8h ago │ 👁️ ✏️ 🗑️│ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Cache Details Modal:**
```jsx
<Modal title="Research Details: Google - Senior Software Engineer">
  <div className="space-y-6">
    <Section title="Company Information">
      <Field label="Company" value="Google LLC" />
      <Field label="Role" value="Senior Software Engineer" />
      <Field label="Industry" value="Technology" />
      <Field label="Company Size" value="100,000+" />
    </Section>
    
    <Section title="Research Data">
      <Field label="Description">
        <p>Google LLC is an American multinational...</p>
      </Field>
      <Field label="Salary Range" value="$150,000 - $250,000" />
    </Section>
    
    <Section title="Metadata">
      <Field label="Data Source" value="Tavily" />
      <Field label="Research Quality" value="95%" />
      <Field label="Cached At" value="2 hours ago" />
      <Field label="Normalized Keys">
        Company: google<br/>
        Role: seniorsoftwareengineer
      </Field>
    </Section>
  </div>
</Modal>
```

### 5. Analytics Dashboard (`/analytics`)

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Header: "Analytics & Insights"                             │
│  ┌──────────────┐                                           │
│  │ Period: ▼   │ Last 7 days | 30 days | All time          │
│  └──────────────┘                                           │
├─────────────────────────────────────────────────────────────┤
│  📊 AI Provider Performance                                 │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Groq (Classifier)                                     │ │
│  │ Success Rate: 95% ███████████████░ 150/158           │ │
│  │ Avg Response: 450ms                                   │ │
│  │ Daily Quota: 45/14,400 used ░░░░░░░░░░░░░░░░░░░░ 0.3%│ │
│  ├───────────────────────────────────────────────────────┤ │
│  │ Tavily (Researcher)                                   │ │
│  │ Success Rate: 100% ████████████████ 33/33            │ │
│  │ Avg Response: 520ms                                   │ │
│  │ Daily Quota: 33/33 used ████████████████████ 100% ⚠️│ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  📈 Performance Trends                                      │
│  ┌─────────────────────────┐ ┌─────────────────────────┐  │
│  │ Response Time Over Time │ │ Success Rate Over Time  │  │
│  │ [Line Chart]            │ │ [Area Chart]            │  │
│  └─────────────────────────┘ └─────────────────────────┘  │
│                                                             │
│  💾 Cache Performance                                       │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Cache Hits vs API Calls (30 days)                    │ │
│  │ [Stacked Area Chart showing cache growth]            │ │
│  │                                                       │ │
│  │ Expected savings: 30-70% after 1 week                │ │
│  │ Current: 0% (just started)                           │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 6. Timeline View (`/timeline`)

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Header: "Application Timeline"                             │
│  ┌──────────────┐                                           │
│  │ View: List ▼│ Grid | Calendar                            │
│  └──────────────┘                                           │
├─────────────────────────────────────────────────────────────┤
│  Today ──────────────────────────────────────────────────  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 2h ago                                                │ │
│  │ 🎯 INTERVIEW - Google                                 │ │
│  │ Senior Software Engineer                              │ │
│  │ Confidence: 85% • Research: ✅                        │ │
│  │ [View Details]                                        │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 5h ago                                                │ │
│  │ 🎉 OFFER - Microsoft                                  │ │
│  │ Staff Engineer                                        │ │
│  │ Confidence: 98% • Research: ✅                        │ │
│  │ [View Details]                                        │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Yesterday ───────────────────────────────────────────────  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 1d ago                                                │ │
│  │ 📝 APPLIED - Amazon                                   │ │
│  │ Principal Engineer                                    │ │
│  │ Confidence: 75% • Research: ✅                        │ │
│  │ [View Details]                                        │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. MetricCard

```jsx
<MetricCard
  title="Total Applications"
  value={11}
  change="+11 from last week"
  trend="up"          // up | down | neutral
  icon={FileTextIcon}
  color="indigo"      // indigo | blue | green | amber | red | violet
/>
```

**Visual:**
```
┌─────────────────────┐
│ 📄 Total Applications│  ← Icon + Title
│                     │
│        11           │  ← Large value
│                     │
│ ↗ +11 from last week│  ← Trend indicator
└─────────────────────┘
```

**Code:**
```jsx
function MetricCard({ title, value, change, trend, icon: Icon, color }) {
  const colorClasses = {
    indigo: 'bg-indigo-50 text-indigo-600',
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    amber: 'bg-amber-50 text-amber-600',
    red: 'bg-red-50 text-red-600',
    violet: 'bg-violet-50 text-violet-600',
  };

  const trendIcons = {
    up: '↗',
    down: '↘',
    neutral: '→',
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
          {change && (
            <p className={`text-sm mt-2 ${trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-600'}`}>
              {trendIcons[trend]} {change}
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

### 2. EventCard

```jsx
<EventCard
  event={{
    id: 1,
    event_type: "INTERVIEW",
    company: "Google",
    role: "Senior Software Engineer",
    confidence: 0.85,
    created_at: "2025-12-13T17:28:25Z",
    has_research: true
  }}
  onView={handleView}
  onEdit={handleEdit}
  onDelete={handleDelete}
/>
```

**Visual:**
```
┌────────────────────────────────────────────┐
│ 🎯 INTERVIEW                          2h ago│
│ Google - Senior Software Engineer          │
│ Confidence: ●●●●○ 85%                      │
│ Research: ✅ Available                     │
│                                            │
│ [View Details] [Edit] [Delete]            │
└────────────────────────────────────────────┘
```

### 3. ConfidenceMeter

```jsx
<ConfidenceMeter value={0.85} showLabel showPercentage />
```

**Visual:**
```
●●●●○ 85%  (High confidence - Green)
●●●○○ 65%  (Medium confidence - Amber)
●○○○○ 45%  (Low confidence - Red)
```

**Code:**
```jsx
function ConfidenceMeter({ value, showLabel = true, showPercentage = true }) {
  const percentage = Math.round(value * 100);
  const dots = 5;
  const filledDots = Math.round(value * dots);
  
  const getColor = (val) => {
    if (val >= 0.8) return 'text-green-500';
    if (val >= 0.6) return 'text-amber-500';
    return 'text-red-500';
  };

  return (
    <div className="flex items-center gap-2">
      <div className={`flex gap-0.5 ${getColor(value)}`}>
        {Array.from({ length: dots }).map((_, i) => (
          <span key={i} className="text-xl">
            {i < filledDots ? '●' : '○'}
          </span>
        ))}
      </div>
      {showPercentage && (
        <span className={`text-sm font-medium ${getColor(value)}`}>
          {percentage}%
        </span>
      )}
      {showLabel && (
        <span className="text-xs text-gray-500">
          {value >= 0.8 ? 'High' : value >= 0.6 ? 'Medium' : 'Low'}
        </span>
      )}
    </div>
  );
}
```

### 4. EventTypeBadge

```jsx
<EventTypeBadge type="INTERVIEW" />
<EventTypeBadge type="OFFER" />
<EventTypeBadge type="APPLIED" />
<EventTypeBadge type="REJECTION" />
```

**Visual:**
```
[🎯 INTERVIEW]  - Blue background
[🎉 OFFER]      - Green background
[📝 APPLIED]    - Amber background
[❌ REJECTION]  - Red background
```

**Code:**
```jsx
function EventTypeBadge({ type }) {
  const config = {
    INTERVIEW: { icon: '🎯', color: 'bg-blue-100 text-blue-700' },
    OFFER: { icon: '🎉', color: 'bg-green-100 text-green-700' },
    APPLIED: { icon: '📝', color: 'bg-amber-100 text-amber-700' },
    REJECTION: { icon: '❌', color: 'bg-red-100 text-red-700' },
  };

  const { icon, color } = config[type] || config.APPLIED;

  return (
    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${color}`}>
      <span>{icon}</span>
      <span>{type}</span>
    </span>
  );
}
```

### 5. FilterPanel

```jsx
<FilterPanel
  filters={filters}
  onChange={handleFilterChange}
  onClear={handleClearFilters}
/>
```

**Sections:**
- Event Type (Checkboxes)
- Date Range (Date picker)
- Confidence (Range slider)
- Company (Autocomplete)
- Research Status (Checkboxes)

### 6. DataTable

```jsx
<DataTable
  columns={[
    { key: 'event_type', label: 'Status', sortable: true, render: EventTypeCell },
    { key: 'company', label: 'Company', sortable: true },
    { key: 'role', label: 'Role', sortable: false },
    { key: 'confidence', label: 'Confidence', sortable: true, render: ConfidenceCell },
    { key: 'created_at', label: 'Date', sortable: true, render: DateCell },
    { key: 'actions', label: 'Actions', render: ActionsCell },
  ]}
  data={events}
  onSort={handleSort}
  onRowClick={handleRowClick}
/>
```

---

## Color Coding & Icons

### Event Type Icons & Colors

| Type | Icon | Color | Hex | Usage |
|------|------|-------|-----|-------|
| INTERVIEW | 🎯 | Blue | #3B82F6 | Badges, Timeline markers |
| OFFER | 🎉 | Green | #10B981 | Badges, Success indicators |
| APPLIED | 📝 | Amber | #F59E0B | Badges, Pending states |
| REJECTION | ❌ | Red | #EF4444 | Badges, Error states |

### Data Source Icons

| Source | Icon | Color | Description |
|--------|------|-------|-------------|
| Tavily | 🔬 | Purple | Research provider |
| Google | 🔍 | Blue | Custom search |
| DuckDuckGo | 🦆 | Orange | Search engine |
| Cache | 💾 | Violet | Local cache hit |
| Manual | ✏️ | Gray | User-added |

### Status Indicators

| Status | Indicator | Description |
|--------|-----------|-------------|
| Available | ✅ | Research available |
| Unavailable | ⚠️ | No research |
| Loading | ⏳ | Fetching research |
| Cached | 💾 | From cache |
| Live API | 🌐 | From live API |
| Error | ❌ | Failed |

---

## Data Visualization

### 1. Event Timeline (Area Chart)

**Library:** Recharts  
**Type:** AreaChart  
**X-Axis:** Date  
**Y-Axis:** Number of events  
**Colors:** Stacked by event type

```jsx
<ResponsiveContainer width="100%" height={300}>
  <AreaChart data={timelineData}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="date" />
    <YAxis />
    <Tooltip />
    <Legend />
    <Area type="monotone" dataKey="INTERVIEW" stackId="1" stroke="#3B82F6" fill="#3B82F6" />
    <Area type="monotone" dataKey="OFFER" stackId="1" stroke="#10B981" fill="#10B981" />
    <Area type="monotone" dataKey="APPLIED" stackId="1" stroke="#F59E0B" fill="#F59E0B" />
    <Area type="monotone" dataKey="REJECTION" stackId="1" stroke="#EF4444" fill="#EF4444" />
  </AreaChart>
</ResponsiveContainer>
```

### 2. Event Distribution (Donut Chart)

**Library:** Recharts  
**Type:** PieChart with inner radius  
**Colors:** Event type colors  
**Labels:** Percentage + count

```jsx
<ResponsiveContainer width="100%" height={300}>
  <PieChart>
    <Pie
      data={distributionData}
      cx="50%"
      cy="50%"
      innerRadius={60}
      outerRadius={100}
      fill="#8884d8"
      paddingAngle={5}
      dataKey="value"
      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
    >
      {distributionData.map((entry, index) => (
        <Cell key={`cell-${index}`} fill={entry.color} />
      ))}
    </Pie>
    <Tooltip />
    <Legend />
  </PieChart>
</ResponsiveContainer>
```

### 3. Top Companies (Bar Chart)

**Library:** Recharts  
**Type:** BarChart  
**X-Axis:** Company name  
**Y-Axis:** Count  
**Color:** Indigo gradient

```jsx
<ResponsiveContainer width="100%" height={300}>
  <BarChart data={companiesData}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="company" />
    <YAxis />
    <Tooltip />
    <Bar dataKey="count" fill="#6366F1" radius={[8, 8, 0, 0]}>
      {companiesData.map((entry, index) => (
        <Cell key={`cell-${index}`} fill={`hsl(240, ${70 - index * 10}%, ${50 + index * 5}%)`} />
      ))}
    </Bar>
  </BarChart>
</ResponsiveContainer>
```

### 4. Provider Performance (Progress Bars)

**Type:** Horizontal progress bars with labels  
**Colors:** Green (success), Red (error)

```jsx
<div className="space-y-4">
  {providers.map(provider => (
    <div key={provider.name}>
      <div className="flex justify-between mb-1">
        <span className="text-sm font-medium">{provider.name}</span>
        <span className="text-sm text-gray-500">{provider.success_rate}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${provider.success_rate >= 90 ? 'bg-green-500' : 'bg-amber-500'}`}
          style={{ width: `${provider.success_rate}%` }}
        />
      </div>
      <div className="flex justify-between mt-1 text-xs text-gray-500">
        <span>Avg: {provider.avg_response_ms}ms</span>
        <span>{provider.used_today}/{provider.daily_limit} quota</span>
      </div>
    </div>
  ))}
</div>
```

---

## Responsive Design

### Breakpoints

```css
sm:  640px   /* Mobile landscape */
md:  768px   /* Tablet */
lg:  1024px  /* Desktop */
xl:  1280px  /* Large desktop */
2xl: 1536px  /* Extra large desktop */
```

### Mobile Layout (< 768px)

- Sidebar collapses to hamburger menu
- Metric cards stack vertically (1 column)
- Tables become card lists
- Charts scale to full width
- Filters move to bottom sheet/modal

### Tablet Layout (768px - 1024px)

- Sidebar becomes drawer (toggleable)
- Metric cards in 2 columns
- Tables remain but with horizontal scroll
- Charts in single column

### Desktop Layout (> 1024px)

- Full sidebar visible
- Metric cards in 3 columns
- Full table view
- Charts in 2-column grid

---

## User Flows

### 1. View Event Flow

```
Dashboard → Click Event Card → Event Details Modal
  ↓
  View Research → Expand Research Section
  ↓
  Edit Event (optional) → Update Modal → Save
  ↓
  Close Modal → Return to Dashboard
```

### 2. Filter Events Flow

```
Events List → Click Filters → Filter Panel Opens
  ↓
  Select Event Type → Apply Filter → Table Updates
  ↓
  Select Date Range → Apply Filter → Table Updates
  ↓
  Adjust Confidence → Apply Filter → Table Updates
  ↓
  Clear Filters (optional) → Table Resets
```

### 3. View Analytics Flow

```
Analytics Page → Select Time Period (7d/30d/All)
  ↓
  View Provider Performance → Expand Provider Details
  ↓
  Check Cache Performance → View Cache Trends
  ↓
  Export Report (optional) → Download PDF/CSV
```

---

**Last Updated:** December 13, 2025  
**Next Steps:** Implement components and integrate with API routes

For API integration, see [API_ROUTES_SPECIFICATION.md](./API_ROUTES_SPECIFICATION.md)  
For database queries, see [DATABASE_SCHEMA_DOCUMENTATION.md](./DATABASE_SCHEMA_DOCUMENTATION.md)
