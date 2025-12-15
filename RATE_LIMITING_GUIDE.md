# 🚦 Rate Limiting Implementation Guide

**Status**: ✅ **IMPLEMENTED AND TESTED**  
**Date**: December 10, 2025  

---

## 📊 Discovery: Gemini Free Tier Actual Limits

### What We Thought
- 15 requests per minute ✅
- 1500 requests per day ❌

### What We Found (After Testing)
```json
{
  "quota_metric": "generate_content_free_tier_requests",
  "quota_id": "GenerateRequestsPerDayPerProjectPerModel-FreeTier",
  "quota_value": 20,
  "model": "gemini-2.5-flash"
}
```

**Real Limits**:
- ✅ **15 requests per minute** (RPM)
- ⚠️ **20 requests per DAY** (RPD) - **CRITICAL**
- ✅ 1 million tokens per minute

**Impact**: Free tier is suitable for **light development** only, not production use.

---

## 🛠️ Implemented Solutions

### 1. Reduced Batch Size ✅

**File**: `services/ingestion/src/main.py`

```python
class IngestionConfig(BaseConfig):
    SERVICE_NAME: str = "ingestion"
    POLL_INTERVAL_SECONDS: int = 60
    BATCH_SIZE: int = 15  # Reduced from 50 to respect API limits
    BATCH_TIMEOUT_SECONDS: int = 30
```

**Why 15?**
- Stays under 15 RPM limit
- Processes in 60 seconds (4s per email)
- Leaves buffer for retries

---

### 2. Automatic Rate Limiting ✅

**File**: `libs/core/llm_client.py`

#### Initialization
```python
class GeminiProvider(LLMProvider):
    def __init__(self):
        self.api_keys = [k.strip() for k in config.GOOGLE_API_KEY.split(',')]
        self.current_key_index = 0
        self.last_request_time = 0  # NEW: Track last request
        self.min_request_interval = 4.0  # NEW: 15 RPM = 4s per request
        
        logger.info(f"⏱️  Rate limit: {self.min_request_interval}s between requests (15 RPM)")
```

#### Request Throttling
```python
def generate(self, prompt: str, json_mode: bool = False) -> str:
    import time
    
    # Ensure minimum time between requests
    time_since_last_request = time.time() - self.last_request_time
    if time_since_last_request < self.min_request_interval:
        sleep_time = self.min_request_interval - time_since_last_request
        logger.debug(f"⏸️  Rate limiting: sleeping {sleep_time:.1f}s")
        time.sleep(sleep_time)
    
    # Make request
    self.last_request_time = time.time()
    response = self.model.generate_content(prompt, ...)
    return response.text
```

**Benefits**:
- ✅ Automatic pacing (4 seconds between calls)
- ✅ No manual delays needed
- ✅ Prevents rate limit errors

---

### 3. Exponential Backoff ✅

**File**: `libs/core/llm_client.py`

```python
except Exception as e:
    error_str = str(e)
    if "429" in error_str or "quota" in error_str.lower():
        attempts += 1
        # Exponential backoff: 10s → 20s → 40s
        backoff_time = min(5 * (2 ** attempts), 60)  # Max 60s
        logger.warning(f"⚠️  Rate limit hit, waiting {backoff_time}s...")
        time.sleep(backoff_time)
        
        if attempts < max_attempts:
            logger.warning(f"Rotating to next API key...")
            self._rotate_key()
            continue
```

**Progression**:
1. First error: Wait 10 seconds
2. Second error: Wait 20 seconds
3. Third error: Wait 40 seconds
4. Max wait: 60 seconds

---

### 4. API Key Rotation ✅

**File**: `libs/core/llm_client.py`

```python
def _rotate_key(self):
    """Rotate to next API key on quota exhaustion"""
    self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
    new_key = self.api_keys[self.current_key_index]
    genai.configure(api_key=new_key)
    logger.info(f"Rotated to API key #{self.current_key_index + 1}/{len(self.api_keys)}")
```

**Configuration** (in `deploy/.env`):
```bash
# Single key
GOOGLE_API_KEY=AIzaSyABC123...

# Multiple keys (comma-separated)
GOOGLE_API_KEY=AIzaSyABC123...,AIzaSyDEF456...,AIzaSyGHI789...
```

**Daily Quota Multiplication**:
- 1 key = 20 emails/day
- 3 keys = 60 emails/day
- 5 keys = 100 emails/day

---

### 5. Enhanced Test Script ✅

**File**: `test_pipeline.py`

```python
# Default: 15 emails (respects rate limits)
python3 test_pipeline.py

# Custom total count
python3 test_pipeline.py 10

# Custom distribution
python3 test_pipeline.py 5 3 2 1  # 5 APPLIED, 3 INTERVIEW, 2 OFFER, 1 REJECTION
```

**Output**:
```
📧 Batch size: 15 emails
   - APPLIED: 9
   - INTERVIEW: 3
   - OFFER: 2
   - REJECTION: 1
⏱️  Expected processing time: ~1.0 minutes (4s per email)
```

---

## 📈 Performance Metrics

### Before Rate Limiting
```
Batch: 50 emails
Result: ❌ 5 classified, 45 failed
Error: "429 You exceeded your current quota"
Time: ~15 seconds (then all failures)
```

### After Rate Limiting
```
Batch: 15 emails
Result: ⚠️ Limited by daily quota (20/day)
Processing: 4s per email = 60s total
Error Handling: ✅ Exponential backoff + key rotation
```

### With Mock Provider (Testing)
```
Batch: Unlimited
Result: ✅ All classified successfully
Processing: <1s per email
Perfect for: Development and demos
```

---

## 🎯 Usage Recommendations

### For Development/Testing ⭐ RECOMMENDED
```bash
# Use Mock Provider
LLM_PROVIDER=mock
```

**Advantages**:
- ✅ Unlimited emails
- ✅ Instant classification
- ✅ No API costs
- ✅ Perfect for demos

### For Production (Low Volume)
```bash
# Use Gemini with rate limiting
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_key_here
```

**Suitable for**:
- ✅ Personal use (≤20 emails/day)
- ✅ Testing with real API
- ✅ $0 cost

**Not suitable for**:
- ❌ Batch processing
- ❌ High-volume testing
- ❌ Demo sessions

### For Production (High Volume)
```bash
# Option A: Upgrade Gemini to Paid
LLM_PROVIDER=gemini
GOOGLE_API_KEY=paid_tier_key

# Option B: Switch to Groq (14,400/day free)
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_key
```

---

## 🔧 Monitoring Rate Limits

### Check Current Usage
```bash
cd deploy
docker-compose logs classifier | grep -E "Rate|quota|429"
```

### Identify Daily Quota Exhaustion
```
⚠️  Rate limit hit on key #1, waiting 10s...
❌ Quota exceeded for metric: generate_content_free_tier_requests
📊 quota_value: 20
⏰ Please retry in 54 seconds
```

**What this means**: Daily quota hit, need to wait until midnight UTC.

### Check Processing Speed
```bash
docker-compose logs classifier | grep "classified" | tail -20
```

**Look for**:
```
✓ Successfully classified with Gemini [0.45s]  # Good
⏸️  Rate limiting: sleeping 3.5s                # Working as expected
```

---

## 🚨 Error Handling

### Error: 429 Quota Exceeded (Per Minute)
```
Solution: ✅ Already handled by rate limiting (4s delay)
Action: None needed, system auto-adjusts
```

### Error: 429 Quota Exceeded (Per Day)
```
Solution: Wait until midnight UTC OR use alternative
Action: 
  1. Switch to LLM_PROVIDER=mock for testing
  2. OR use multiple API keys
  3. OR upgrade to paid tier
  4. OR switch to Groq
```

### Error: All API Keys Exhausted
```
Solution: All keys hit daily quota
Action:
  1. Wait for quota reset (midnight UTC)
  2. Add more API keys
  3. Switch provider temporarily
```

---

## 📊 Cost Analysis

### Free Tier Comparison

| Provider | RPM | RPD | Cost | Best For |
|----------|-----|-----|------|----------|
| **Gemini** | 15 | **20** | $0 | Light dev |
| **Groq** | 30 | **14,400** | $0 | Heavy dev |
| **Mock** | ∞ | ∞ | $0 | Testing |

### Paid Tier Comparison

| Provider | Cost/Request | 1000 emails/mo | Notes |
|----------|-------------|----------------|-------|
| **Gemini** | $0.00025 | ~$0.25 | Affordable |
| **GPT-4o Mini** | $0.00015 | ~$0.15 | Cheaper |
| **Groq** | $0.00027 | ~$0.27 | Fastest |

---

## ✅ Implementation Checklist

- [x] Reduce batch size to 15 emails
- [x] Add rate limiting (4s between requests)
- [x] Implement exponential backoff
- [x] Support multiple API keys
- [x] Test with 15-email batch
- [x] Document actual quota limits
- [x] Add usage monitoring
- [x] Update test script with custom sizes
- [x] Create this guide

---

## 🔄 Next Steps

1. **For Continued Testing**:
   ```bash
   # Switch to mock provider
   LLM_PROVIDER=mock
   docker-compose up -d --force-recreate classifier
   ```

2. **For Production**:
   - Get Groq API key: https://console.groq.com/
   - OR upgrade Gemini to paid tier
   - OR use multiple Gemini keys

3. **Monitor Usage**:
   - Track daily quota: https://ai.dev/usage?tab=rate-limit
   - Set up alerts for quota exhaustion
   - Review logs daily

---

## 📚 References

- [Gemini API Rate Limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Gemini Pricing](https://ai.google.dev/pricing)
- [Groq Console](https://console.groq.com/)
- [Monitor Gemini Usage](https://ai.dev/usage?tab=rate-limit)

---

**Last Updated**: December 10, 2025  
**Tested With**: Gemini 2.5-Flash, 15-email batches  
**Status**: ✅ Production-ready rate limiting implemented
