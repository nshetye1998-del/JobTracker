# 🚀 Job Tracker Career AI - API Routes Specification

**Version:** 1.0  
**Date:** December 13, 2025  
**Base URL:** `http://localhost:8000`

---

## 📑 Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Events API](#events-api)
4. [Research Cache API](#research-cache-api)
5. [Analytics API](#analytics-api)
6. [Provider API](#provider-api)
7. [System Health API](#system-health-api)
8. [Error Handling](#error-handling)
9. [Response Formats](#response-formats)

---

## API Overview

### Base Configuration
- **Protocol:** HTTP/HTTPS
- **Port:** 8000 (Dashboard API)
- **Format:** JSON
- **Authentication:** JWT Bearer Token (recommended)
- **Rate Limiting:** 100 requests/minute per IP

### Standard Response Format
```json
{
  "success": true,
  "data": { /* response data */ },
  "meta": {
    "timestamp": "2025-12-13T17:30:00Z",
    "version": "1.0"
  }
}
```

---

## Authentication

### 1. Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123"
}

Response 200:
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "Nikunj Shetye"
    },
    "expires_at": "2025-12-14T17:30:00Z"
  }
}
```

### 2. Logout
```http
POST /api/auth/logout
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "message": "Logged out successfully"
}
```

### 3. Get Current User
```http
GET /api/auth/me
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "data": {
    "id": 1,
    "email": "user@example.com",
    "name": "Nikunj Shetye",
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

---

## Events API

### 1. List All Events (Paginated)
```http
GET /api/events?page=1&limit=20&event_type=INTERVIEW&sort_by=created_at&sort_order=desc

Query Parameters:
- page (integer, default: 1) - Page number
- limit (integer, default: 20, max: 100) - Items per page
- event_type (string, optional) - Filter: APPLIED|INTERVIEW|OFFER|REJECTION
- company (string, optional) - Filter by company name
- date_from (ISO date, optional) - Start date filter
- date_to (ISO date, optional) - End date filter
- min_confidence (float, optional) - Minimum confidence (0-1)
- has_research (boolean, optional) - Filter events with research
- sort_by (string, default: created_at) - Sort field
- sort_order (string, default: desc) - asc|desc

Response 200:
{
  "success": true,
  "data": {
    "events": [
      {
        "id": 1,
        "event_id": "cls_19b13ecc78c161bc",
        "event_type": "INTERVIEW",
        "company": "Google",
        "role": "Senior Software Engineer",
        "confidence": 0.85,
        "summary": "Interview invitation from Google",
        "has_research": true,
        "created_at": "2025-12-13T17:28:25.184845Z",
        "classification_method": "ai",
        "classification_provider": "groq"
      }
    ],
    "pagination": {
      "total": 11,
      "page": 1,
      "limit": 20,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  }
}
```

### 2. Get Single Event
```http
GET /api/events/:id

Response 200:
{
  "success": true,
  "data": {
    "id": 1,
    "event_id": "cls_19b13ecc78c161bc",
    "event_type": "INTERVIEW",
    "company": "Google",
    "role": "Senior Software Engineer",
    "confidence": 0.85,
    "summary": "Interview invitation from Google",
    "raw_data": {
      "event_id": "cls_19b13ecc78c161bc",
      "message_id": "19b13ecc78c161bc",
      "company": "Google",
      "role": "Senior Software Engineer",
      "confidence": 0.85,
      "classified_at": "2025-12-13T17:28:25.184845",
      "metadata": {
        "method": "ai",
        "provider": "groq",
        "snippet": "Dear Nikunj, Thank you for your interest..."
      }
    },
    "research_briefing": "Google is a multinational technology company...",
    "research_metadata": {
      "provider": "tavily",
      "match_type": "exact",
      "cached": true,
      "quality": 0.95,
      "response_time_ms": 450
    },
    "created_at": "2025-12-13T17:28:25.184845Z",
    "updated_at": "2025-12-13T17:30:00.000000Z"
  }
}
```

### 3. Event Statistics
```http
GET /api/events/stats

Response 200:
{
  "success": true,
  "data": {
    "total": 11,
    "by_type": {
      "APPLIED": 1,
      "INTERVIEW": 7,
      "OFFER": 3,
      "REJECTION": 0
    },
    "by_type_percentage": {
      "APPLIED": 9.1,
      "INTERVIEW": 63.6,
      "OFFER": 27.3,
      "REJECTION": 0
    },
    "this_week": 11,
    "this_month": 11,
    "avg_confidence": 0.87,
    "researched_count": 10,
    "research_percentage": 90.9
  }
}
```

### 4. Timeline Data
```http
GET /api/events/timeline?days=30

Query Parameters:
- days (integer, default: 30) - Number of days to include

Response 200:
{
  "success": true,
  "data": {
    "timeline": [
      {
        "date": "2025-12-13",
        "APPLIED": 1,
        "INTERVIEW": 5,
        "OFFER": 2,
        "REJECTION": 0,
        "total": 8
      },
      {
        "date": "2025-12-12",
        "APPLIED": 0,
        "INTERVIEW": 2,
        "OFFER": 1,
        "REJECTION": 0,
        "total": 3
      }
    ]
  }
}
```

### 5. Search Events
```http
GET /api/events/search?q=google&fields=company,role

Query Parameters:
- q (string, required) - Search query
- fields (string, optional) - Comma-separated fields to search (company,role,summary)

Response 200:
{
  "success": true,
  "data": {
    "results": [
      {
        "id": 1,
        "event_type": "INTERVIEW",
        "company": "Google",
        "role": "Senior Software Engineer",
        "confidence": 0.85,
        "created_at": "2025-12-13T17:28:25Z"
      }
    ],
    "count": 1
  }
}
```

### 6. Update Event
```http
PATCH /api/events/:id
Content-Type: application/json

{
  "summary": "Updated summary",
  "confidence": 0.9
}

Response 200:
{
  "success": true,
  "data": {
    "id": 1,
    "updated_fields": ["summary", "confidence"],
    "updated_at": "2025-12-13T18:00:00Z"
  }
}
```

### 7. Delete Event
```http
DELETE /api/events/:id

Response 200:
{
  "success": true,
  "message": "Event deleted successfully",
  "data": {
    "deleted_id": 1
  }
}
```

---

## Research Cache API

### 1. List Cached Research
```http
GET /api/research?page=1&limit=20&company=google&data_source=tavily

Query Parameters:
- page (integer, default: 1)
- limit (integer, default: 20, max: 100)
- company (string, optional) - Filter by company
- role (string, optional) - Filter by role
- data_source (string, optional) - tavily|google|duckduckgo
- min_quality (float, optional) - Minimum quality (0-1)
- date_from (ISO date, optional)
- date_to (ISO date, optional)

Response 200:
{
  "success": true,
  "data": {
    "research": [
      {
        "id": 1,
        "company": "Google",
        "role": "Senior Software Engineer",
        "description": "Google LLC is an American multinational...",
        "salary_range": "$150,000 - $250,000",
        "industry": "Technology",
        "company_size": "100,000+",
        "data_source": "tavily",
        "research_quality": 0.95,
        "researched_at": "2025-12-13T17:30:00Z"
      }
    ],
    "pagination": {
      "total": 3,
      "page": 1,
      "limit": 20,
      "total_pages": 1
    }
  }
}
```

### 2. Get Single Research Entry
```http
GET /api/research/:id

Response 200:
{
  "success": true,
  "data": {
    "id": 1,
    "company": "Google",
    "role": "Senior Software Engineer",
    "description": "Google LLC is an American multinational...",
    "salary_range": "$150,000 - $250,000",
    "industry": "Technology",
    "company_size": "100,000+",
    "data_source": "tavily",
    "research_quality": 0.95,
    "researched_at": "2025-12-13T17:30:00Z",
    "company_normalized": "google",
    "role_normalized": "seniorsoftwareengineer"
  }
}
```

### 3. Cache Statistics
```http
GET /api/research/stats

Response 200:
{
  "success": true,
  "data": {
    "total_cached": 3,
    "unique_companies": 3,
    "unique_roles": 3,
    "by_data_source": {
      "tavily": 3,
      "google": 0,
      "duckduckgo": 0
    },
    "by_data_source_percentage": {
      "tavily": 100.0,
      "google": 0,
      "duckduckgo": 0
    },
    "avg_quality": 0.95,
    "cache_hit_rate": 0.0,
    "oldest_entry": "2025-12-13T15:00:00Z",
    "newest_entry": "2025-12-13T17:30:00Z"
  }
}
```

### 4. List Unique Companies
```http
GET /api/research/companies

Response 200:
{
  "success": true,
  "data": {
    "companies": [
      {
        "company": "Google",
        "cached_count": 1,
        "data_source": "tavily",
        "avg_quality": 0.95
      },
      {
        "company": "Microsoft",
        "cached_count": 1,
        "data_source": "tavily",
        "avg_quality": 0.95
      }
    ]
  }
}
```

### 5. List Unique Roles
```http
GET /api/research/roles

Response 200:
{
  "success": true,
  "data": {
    "roles": [
      {
        "role": "Senior Software Engineer",
        "cached_count": 2,
        "avg_quality": 0.92
      },
      {
        "role": "Staff Engineer",
        "cached_count": 1,
        "avg_quality": 0.95
      }
    ]
  }
}
```

### 6. Search Cache
```http
GET /api/research/search?q=google

Query Parameters:
- q (string, required) - Search query

Response 200:
{
  "success": true,
  "data": {
    "results": [
      {
        "id": 1,
        "company": "Google",
        "role": "Senior Software Engineer",
        "research_quality": 0.95,
        "data_source": "tavily"
      }
    ],
    "count": 1
  }
}
```

### 7. Add Research (Admin)
```http
POST /api/research
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "company": "Amazon",
  "role": "Principal Engineer",
  "description": "Amazon.com, Inc. is an American multinational...",
  "salary_range": "$200,000 - $350,000",
  "industry": "Technology",
  "company_size": "1,000,000+",
  "data_source": "manual"
}

Response 201:
{
  "success": true,
  "data": {
    "id": 4,
    "company": "Amazon",
    "research_quality": 0.85,
    "researched_at": "2025-12-13T18:00:00Z"
  }
}
```

### 8. Delete Research (Admin)
```http
DELETE /api/research/:id
Authorization: Bearer {admin_token}

Response 200:
{
  "success": true,
  "message": "Research entry deleted successfully"
}
```

---

## Analytics API

### 1. Dashboard Overview
```http
GET /api/analytics/overview

Response 200:
{
  "success": true,
  "data": {
    "total_events": 11,
    "by_type": {
      "APPLIED": 1,
      "INTERVIEW": 7,
      "OFFER": 3,
      "REJECTION": 0
    },
    "this_week": 11,
    "this_month": 11,
    "growth": {
      "weekly_change": 11,
      "monthly_change": 11,
      "weekly_percentage": 100.0
    },
    "cache_stats": {
      "total_cached": 3,
      "unique_companies": 3,
      "cache_hit_rate": 0.0,
      "expected_savings": "30-70%"
    },
    "top_companies": [
      {"company": "Google", "count": 5},
      {"company": "Microsoft", "count": 3},
      {"company": "Amazon", "count": 2}
    ],
    "success_rate": {
      "offers": 3,
      "total_applications": 11,
      "percentage": 27.3
    }
  }
}
```

### 2. Provider Performance
```http
GET /api/analytics/providers?days=7

Query Parameters:
- days (integer, default: 7) - Number of days to analyze

Response 200:
{
  "success": true,
  "data": {
    "providers": [
      {
        "name": "groq",
        "type": "classifier",
        "total_requests": 150,
        "successful_requests": 142,
        "failed_requests": 8,
        "success_rate": 94.7,
        "avg_response_time_ms": 450,
        "daily_limit": 14400,
        "used_today": 45,
        "quota_remaining": 14355,
        "quota_percentage": 0.3
      },
      {
        "name": "tavily",
        "type": "researcher",
        "total_requests": 33,
        "successful_requests": 33,
        "failed_requests": 0,
        "success_rate": 100.0,
        "avg_response_time_ms": 520,
        "daily_limit": 33,
        "used_today": 33,
        "quota_remaining": 0,
        "quota_percentage": 100.0,
        "status": "exhausted"
      }
    ]
  }
}
```

### 3. Time-Series Trends
```http
GET /api/analytics/trends?metric=events&days=30

Query Parameters:
- metric (string, required) - events|confidence|response_time
- days (integer, default: 30) - Number of days

Response 200:
{
  "success": true,
  "data": {
    "metric": "events",
    "period": "30 days",
    "data_points": [
      {
        "date": "2025-12-13",
        "value": 8,
        "breakdown": {
          "APPLIED": 1,
          "INTERVIEW": 5,
          "OFFER": 2
        }
      }
    ]
  }
}
```

### 4. Cache Performance
```http
GET /api/analytics/cache-performance?days=7

Response 200:
{
  "success": true,
  "data": {
    "cache_hit_rate": 0.0,
    "total_researches": 10,
    "cache_hits": 0,
    "api_calls": 10,
    "avg_cache_response_ms": 0,
    "avg_api_response_ms": 520,
    "performance_gain": "500x faster when cached",
    "daily_breakdown": [
      {
        "date": "2025-12-13",
        "cache_hits": 0,
        "api_calls": 10,
        "hit_rate": 0.0
      }
    ]
  }
}
```

### 5. Events by Type
```http
GET /api/analytics/events-by-type

Response 200:
{
  "success": true,
  "data": {
    "distribution": [
      {
        "event_type": "INTERVIEW",
        "count": 7,
        "percentage": 63.6,
        "avg_confidence": 0.87
      },
      {
        "event_type": "OFFER",
        "count": 3,
        "percentage": 27.3,
        "avg_confidence": 0.92
      },
      {
        "event_type": "APPLIED",
        "count": 1,
        "percentage": 9.1,
        "avg_confidence": 0.75
      }
    ]
  }
}
```

### 6. Events by Company
```http
GET /api/analytics/events-by-company?limit=10

Query Parameters:
- limit (integer, default: 10) - Top N companies

Response 200:
{
  "success": true,
  "data": {
    "companies": [
      {
        "company": "Google",
        "total_events": 5,
        "interviews": 3,
        "offers": 2,
        "applied": 0,
        "rejections": 0,
        "offer_rate": 40.0
      },
      {
        "company": "Microsoft",
        "total_events": 3,
        "interviews": 2,
        "offers": 1,
        "applied": 0,
        "rejections": 0,
        "offer_rate": 33.3
      }
    ]
  }
}
```

### 7. Response Times
```http
GET /api/analytics/response-times?days=7

Response 200:
{
  "success": true,
  "data": {
    "by_provider": [
      {
        "provider": "groq",
        "avg_response_ms": 450,
        "min_response_ms": 320,
        "max_response_ms": 680,
        "p50_ms": 440,
        "p95_ms": 620,
        "p99_ms": 670
      },
      {
        "provider": "tavily",
        "avg_response_ms": 520,
        "min_response_ms": 400,
        "max_response_ms": 750,
        "p50_ms": 510,
        "p95_ms": 680,
        "p99_ms": 740
      }
    ]
  }
}
```

---

## Provider API

### 1. List All Providers
```http
GET /api/providers

Response 200:
{
  "success": true,
  "data": {
    "providers": [
      {
        "name": "groq",
        "type": "classifier",
        "model": "llama-3.1-8b-instant",
        "status": "active",
        "daily_limit": 14400,
        "used_today": 45,
        "success_rate": 94.7,
        "avg_response_ms": 450
      },
      {
        "name": "gemini",
        "type": "classifier",
        "model": "gemini-pro",
        "status": "backup",
        "daily_limit": 1500,
        "used_today": 0,
        "success_rate": 100.0,
        "avg_response_ms": 380
      },
      {
        "name": "tavily",
        "type": "researcher",
        "status": "exhausted",
        "daily_limit": 33,
        "used_today": 33,
        "success_rate": 100.0,
        "avg_response_ms": 520
      }
    ]
  }
}
```

### 2. Single Provider Stats
```http
GET /api/providers/:name

Response 200:
{
  "success": true,
  "data": {
    "name": "groq",
    "type": "classifier",
    "model": "llama-3.1-8b-instant",
    "status": "active",
    "limits": {
      "daily_requests": 14400,
      "requests_per_minute": 30,
      "tokens_per_minute": 6000
    },
    "usage": {
      "today": 45,
      "this_hour": 12,
      "remaining_today": 14355
    },
    "performance": {
      "total_requests": 150,
      "successful": 142,
      "failed": 8,
      "success_rate": 94.7,
      "avg_response_ms": 450
    },
    "quota_resets_at": "2025-12-14T00:00:00Z"
  }
}
```

### 3. Provider Usage History
```http
GET /api/providers/:name/usage?days=7

Response 200:
{
  "success": true,
  "data": {
    "provider": "groq",
    "period": "7 days",
    "usage": [
      {
        "date": "2025-12-13",
        "total_requests": 45,
        "successful": 43,
        "failed": 2,
        "avg_response_ms": 450
      }
    ],
    "totals": {
      "total_requests": 150,
      "successful": 142,
      "failed": 8,
      "success_rate": 94.7
    }
  }
}
```

### 4. Provider Comparison
```http
GET /api/providers/comparison

Response 200:
{
  "success": true,
  "data": {
    "classifiers": [
      {
        "name": "groq",
        "success_rate": 94.7,
        "avg_response_ms": 450,
        "cost_per_1k": 0.0,
        "daily_quota_used": 0.3
      },
      {
        "name": "gemini",
        "success_rate": 100.0,
        "avg_response_ms": 380,
        "cost_per_1k": 0.0,
        "daily_quota_used": 0.0
      }
    ],
    "researchers": [
      {
        "name": "tavily",
        "success_rate": 100.0,
        "avg_response_ms": 520,
        "daily_quota_used": 100.0
      },
      {
        "name": "google",
        "success_rate": 98.5,
        "avg_response_ms": 380,
        "daily_quota_used": 0.0
      }
    ]
  }
}
```

---

## System Health API

### 1. Overall Health
```http
GET /api/health

Response 200:
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2025-12-13T18:00:00Z",
    "uptime_seconds": 86400,
    "version": "1.0.0",
    "services": {
      "database": "healthy",
      "kafka": "healthy",
      "redis": "healthy",
      "classifier": "healthy",
      "researcher": "healthy"
    }
  }
}
```

### 2. Service Status
```http
GET /api/health/services

Response 200:
{
  "success": true,
  "data": {
    "services": [
      {
        "name": "classifier",
        "status": "healthy",
        "uptime_seconds": 86400,
        "last_check": "2025-12-13T18:00:00Z"
      },
      {
        "name": "researcher",
        "status": "healthy",
        "uptime_seconds": 86400,
        "last_check": "2025-12-13T18:00:00Z",
        "warnings": ["Tavily quota exhausted"]
      },
      {
        "name": "notifier",
        "status": "degraded",
        "uptime_seconds": 86400,
        "last_check": "2025-12-13T18:00:00Z",
        "warnings": ["WhatsApp rate limited"]
      }
    ]
  }
}
```

### 3. Kafka Status
```http
GET /api/health/kafka

Response 200:
{
  "success": true,
  "data": {
    "status": "healthy",
    "topics": [
      {
        "name": "raw_inbox_stream",
        "partitions": 1,
        "lag": 0,
        "messages_today": 11
      },
      {
        "name": "classified_events",
        "partitions": 1,
        "lag": 0,
        "messages_today": 11
      },
      {
        "name": "notifications",
        "partitions": 1,
        "lag": 0,
        "messages_today": 11
      }
    ]
  }
}
```

### 4. Database Status
```http
GET /api/health/database

Response 200:
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "PostgreSQL 13.23",
    "connections": {
      "active": 5,
      "idle": 10,
      "total": 15
    },
    "tables": {
      "career_events": 11,
      "research_cache": 3,
      "applications": 0,
      "provider_usage": 183
    },
    "database_size_mb": 45.2
  }
}
```

---

## Error Handling

### Standard Error Response
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Event with ID 999 not found",
    "details": null
  },
  "meta": {
    "timestamp": "2025-12-13T18:00:00Z"
  }
}
```

### Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_REQUEST` | Invalid request parameters |
| 401 | `UNAUTHORIZED` | Missing or invalid authentication |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `RESOURCE_NOT_FOUND` | Resource does not exist |
| 409 | `CONFLICT` | Resource already exists |
| 422 | `VALIDATION_ERROR` | Request validation failed |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server error |
| 503 | `SERVICE_UNAVAILABLE` | Service temporarily unavailable |

### Example Error Responses

**400 Bad Request:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid event_type value",
    "details": {
      "field": "event_type",
      "value": "INVALID",
      "allowed": ["APPLIED", "INTERVIEW", "OFFER", "REJECTION"]
    }
  }
}
```

**401 Unauthorized:**
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Missing or invalid authentication token"
  }
}
```

**404 Not Found:**
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Event with ID 999 not found"
  }
}
```

**429 Rate Limit:**
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "details": {
      "limit": 100,
      "window": "60 seconds",
      "retry_after": 45
    }
  }
}
```

---

## Response Formats

### Pagination
All list endpoints support pagination:

```json
{
  "pagination": {
    "total": 150,
    "page": 2,
    "limit": 20,
    "total_pages": 8,
    "has_next": true,
    "has_prev": true,
    "next_page": 3,
    "prev_page": 1
  }
}
```

### Timestamps
All timestamps use ISO 8601 format with UTC timezone:
```
2025-12-13T18:00:00Z
```

### Null Values
- Nullable fields return `null` if no value
- Missing optional fields are omitted from response

### Boolean Values
- `true` / `false` (lowercase)

### Numbers
- Integers: `42`
- Floats: `0.85` (2 decimal places for percentages/confidence)

---

## Best Practices

### 1. Use Pagination
Always use pagination for list endpoints to avoid large responses.

### 2. Filter Early
Apply filters at the API level rather than client-side.

### 3. Cache Responses
Cache GET requests that don't change frequently (e.g., stats, provider info).

### 4. Handle Errors Gracefully
Always check `success` field and handle errors appropriately.

### 5. Use Appropriate HTTP Methods
- GET: Retrieve data (no side effects)
- POST: Create new resources
- PATCH: Partial update
- DELETE: Remove resources

### 6. Request Timeouts
Set reasonable timeouts (30s recommended).

### 7. Retry Logic
Implement exponential backoff for 5xx errors.

---

**Last Updated:** December 13, 2025  
**Next Review:** After implementing authentication

For database schema details, see [DATABASE_SCHEMA_DOCUMENTATION.md](./DATABASE_SCHEMA_DOCUMENTATION.md)
