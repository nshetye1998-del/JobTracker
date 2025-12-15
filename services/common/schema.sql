-- ═══════════════════════════════════════════════════════════════
-- JOB TRACKER PRODUCTION DATABASE SCHEMA
-- ═══════════════════════════════════════════════════════════════
-- This schema supports:
-- 1. Persistent deduplication across restarts
-- 2. Self-learning keyword system
-- 3. Multi-provider performance tracking
-- ═══════════════════════════════════════════════════════════════

-- Existing applications table (keep as is)
CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    email_id VARCHAR(255) UNIQUE NOT NULL,
    subject TEXT,
    body TEXT,
    from_email VARCHAR(255),
    company VARCHAR(255),
    role VARCHAR(255),
    status VARCHAR(50),
    classification VARCHAR(50),
    confidence FLOAT,
    received_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    provider VARCHAR(50) DEFAULT 'gmail'
);

CREATE INDEX IF NOT EXISTS idx_applications_email_id ON applications(email_id);
CREATE INDEX IF NOT EXISTS idx_applications_classification ON applications(classification);
CREATE INDEX IF NOT EXISTS idx_applications_created_at ON applications(created_at);

-- ═══════════════════════════════════════════════════════════════
-- PART 1: DEDUPLICATION SYSTEM
-- ═══════════════════════════════════════════════════════════════

-- NEW: Processed emails tracking (for deduplication)
CREATE TABLE IF NOT EXISTS processed_emails (
    email_id VARCHAR(255) PRIMARY KEY,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50),
    classification VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_processed_email_id ON processed_emails(email_id);
CREATE INDEX IF NOT EXISTS idx_processed_at ON processed_emails(processed_at);

-- ═══════════════════════════════════════════════════════════════
-- PART 2: SELF-LEARNING KEYWORD SYSTEM
-- ═══════════════════════════════════════════════════════════════

-- NEW: Keyword patterns (self-learning system)
CREATE TABLE IF NOT EXISTS keyword_patterns (
    id SERIAL PRIMARY KEY,
    keyword_phrase TEXT NOT NULL,
    classification VARCHAR(50) NOT NULL,
    confidence FLOAT DEFAULT 0.85,
    times_matched INTEGER DEFAULT 0,
    times_correct INTEGER DEFAULT 0,
    accuracy FLOAT DEFAULT 0,
    learned_from VARCHAR(50), -- 'ai', 'user_correction', 'base'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(keyword_phrase, classification)
);

CREATE INDEX IF NOT EXISTS idx_keyword_phrase ON keyword_patterns(keyword_phrase);
CREATE INDEX IF NOT EXISTS idx_classification ON keyword_patterns(classification);
CREATE INDEX IF NOT EXISTS idx_accuracy ON keyword_patterns(accuracy);
CREATE INDEX IF NOT EXISTS idx_is_active ON keyword_patterns(is_active);

-- NEW: Classification feedback (learning from results)
CREATE TABLE IF NOT EXISTS classification_feedback (
    id SERIAL PRIMARY KEY,
    email_id VARCHAR(255),
    classification_method VARCHAR(50), -- 'keyword', 'ai', 'user_correction'
    keyword_id INTEGER REFERENCES keyword_patterns(id),
    initial_classification VARCHAR(50),
    final_classification VARCHAR(50),
    was_correct BOOLEAN,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feedback_email_id ON classification_feedback(email_id);
CREATE INDEX IF NOT EXISTS idx_feedback_method ON classification_feedback(classification_method);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON classification_feedback(created_at);

-- ═══════════════════════════════════════════════════════════════
-- PART 3: MULTI-PROVIDER PERFORMANCE TRACKING
-- ═══════════════════════════════════════════════════════════════

-- NEW: Provider performance tracking
CREATE TABLE IF NOT EXISTS provider_performance (
    id SERIAL PRIMARY KEY,
    provider_name VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN,
    latency_ms INTEGER,
    error_message TEXT,
    quota_remaining INTEGER,
    daily_quota INTEGER
);

CREATE INDEX IF NOT EXISTS idx_provider_timestamp ON provider_performance(provider_name, timestamp);

-- NEW: Daily quota tracking
CREATE TABLE IF NOT EXISTS daily_quota_usage (
    date DATE NOT NULL,
    provider_name VARCHAR(50) NOT NULL,
    calls_made INTEGER DEFAULT 0,
    calls_successful INTEGER DEFAULT 0,
    quota_limit INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (date, provider_name)
);

CREATE INDEX IF NOT EXISTS idx_quota_date ON daily_quota_usage(date);

-- ═══════════════════════════════════════════════════════════════
-- BASE KEYWORD PATTERNS (SEED DATA)
-- ═══════════════════════════════════════════════════════════════

-- Insert base keyword patterns (only if table is empty)
INSERT INTO keyword_patterns (keyword_phrase, classification, confidence, learned_from, times_matched, times_correct) 
SELECT * FROM (VALUES
    -- Interview keywords (high confidence)
    ('interview invitation', 'INTERVIEW', 0.98, 'base', 0, 0),
    ('schedule an interview', 'INTERVIEW', 0.98, 'base', 0, 0),
    ('phone screen', 'INTERVIEW', 0.95, 'base', 0, 0),
    ('technical interview', 'INTERVIEW', 0.96, 'base', 0, 0),
    ('coding interview', 'INTERVIEW', 0.97, 'base', 0, 0),
    ('interview confirmation', 'INTERVIEW', 0.98, 'base', 0, 0),
    ('hiring manager would like', 'INTERVIEW', 0.94, 'base', 0, 0),
    ('meet with the team', 'INTERVIEW', 0.93, 'base', 0, 0),
    ('calendly.com', 'INTERVIEW', 0.92, 'base', 0, 0),
    ('interview scheduled', 'INTERVIEW', 0.98, 'base', 0, 0),
    ('zoom interview', 'INTERVIEW', 0.96, 'base', 0, 0),
    ('teams interview', 'INTERVIEW', 0.96, 'base', 0, 0),
    ('video interview', 'INTERVIEW', 0.95, 'base', 0, 0),
    ('onsite interview', 'INTERVIEW', 0.97, 'base', 0, 0),
    ('interview process', 'INTERVIEW', 0.90, 'base', 0, 0),
    ('next step is', 'INTERVIEW', 0.88, 'base', 0, 0),
    ('move forward with', 'INTERVIEW', 0.89, 'base', 0, 0),
    ('schedule a call', 'INTERVIEW', 0.91, 'base', 0, 0),
    ('chat with', 'INTERVIEW', 0.87, 'base', 0, 0),
    ('speak with you', 'INTERVIEW', 0.88, 'base', 0, 0),
    
    -- Rejection keywords (high confidence)
    ('not moving forward', 'REJECTION', 0.97, 'base', 0, 0),
    ('not selected', 'REJECTION', 0.98, 'base', 0, 0),
    ('other candidates', 'REJECTION', 0.95, 'base', 0, 0),
    ('decided to pursue', 'REJECTION', 0.94, 'base', 0, 0),
    ('better fit', 'REJECTION', 0.93, 'base', 0, 0),
    ('regret to inform', 'REJECTION', 0.98, 'base', 0, 0),
    ('will not be proceeding', 'REJECTION', 0.97, 'base', 0, 0),
    ('position has been filled', 'REJECTION', 0.96, 'base', 0, 0),
    ('thank you for your interest', 'REJECTION', 0.85, 'base', 0, 0),
    ('unfortunately', 'REJECTION', 0.89, 'base', 0, 0),
    ('not the right fit', 'REJECTION', 0.94, 'base', 0, 0),
    ('different direction', 'REJECTION', 0.92, 'base', 0, 0),
    ('will not be moving', 'REJECTION', 0.97, 'base', 0, 0),
    ('wish you the best', 'REJECTION', 0.88, 'base', 0, 0),
    ('keep your resume on file', 'REJECTION', 0.91, 'base', 0, 0),
    
    -- Offer keywords (high confidence)
    ('offer letter', 'OFFER', 0.99, 'base', 0, 0),
    ('pleased to offer', 'OFFER', 0.99, 'base', 0, 0),
    ('employment offer', 'OFFER', 0.99, 'base', 0, 0),
    ('accept our offer', 'OFFER', 0.98, 'base', 0, 0),
    ('extend an offer', 'OFFER', 0.99, 'base', 0, 0),
    ('job offer', 'OFFER', 0.98, 'base', 0, 0),
    ('offer of employment', 'OFFER', 0.99, 'base', 0, 0),
    ('start date', 'OFFER', 0.92, 'base', 0, 0),
    ('compensation package', 'OFFER', 0.95, 'base', 0, 0),
    ('salary', 'OFFER', 0.88, 'base', 0, 0),
    
    -- Application confirmation keywords (medium confidence)
    ('received your application', 'OTHER', 0.85, 'base', 0, 0),
    ('application received', 'OTHER', 0.85, 'base', 0, 0),
    ('reviewing your application', 'OTHER', 0.87, 'base', 0, 0),
    ('thank you for applying', 'OTHER', 0.83, 'base', 0, 0),
    ('application status', 'OTHER', 0.82, 'base', 0, 0)
) AS v(keyword_phrase, classification, confidence, learned_from, times_matched, times_correct)
WHERE NOT EXISTS (SELECT 1 FROM keyword_patterns LIMIT 1)
ON CONFLICT (keyword_phrase, classification) DO NOTHING;

-- ═══════════════════════════════════════════════════════════════
-- UTILITY VIEWS
-- ═══════════════════════════════════════════════════════════════

-- View: Keyword performance
CREATE OR REPLACE VIEW keyword_performance AS
SELECT 
    k.id,
    k.keyword_phrase,
    k.classification,
    k.confidence,
    k.times_matched,
    k.times_correct,
    CASE 
        WHEN k.times_matched > 0 THEN ROUND((k.times_correct::FLOAT / k.times_matched::FLOAT) * 100, 2)
        ELSE 0
    END as accuracy_percentage,
    k.learned_from,
    k.is_active,
    k.last_used_at
FROM keyword_patterns k
ORDER BY k.times_matched DESC;

-- View: Provider performance summary
CREATE OR REPLACE VIEW provider_summary AS
SELECT 
    provider_name,
    COUNT(*) as total_calls,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_calls,
    ROUND(AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) * 100, 2) as success_rate_pct,
    ROUND(AVG(latency_ms), 0) as avg_latency_ms,
    MIN(timestamp) as first_call,
    MAX(timestamp) as last_call
FROM provider_performance
GROUP BY provider_name
ORDER BY total_calls DESC;

-- View: Daily classification efficiency
CREATE OR REPLACE VIEW daily_classification_efficiency AS
SELECT 
    DATE(created_at) as date,
    classification_method,
    COUNT(*) as total_classifications,
    ROUND(AVG(confidence) * 100, 2) as avg_confidence_pct,
    SUM(CASE WHEN was_correct THEN 1 ELSE 0 END) as correct_classifications,
    ROUND(AVG(CASE WHEN was_correct THEN 1.0 ELSE 0.0 END) * 100, 2) as accuracy_pct
FROM classification_feedback
GROUP BY DATE(created_at), classification_method
ORDER BY date DESC, classification_method;

-- ═══════════════════════════════════════════════════════════════
-- MAINTENANCE FUNCTIONS
-- ═══════════════════════════════════════════════════════════════

-- Function: Update keyword accuracy (called periodically)
CREATE OR REPLACE FUNCTION update_keyword_accuracy()
RETURNS void AS $$
BEGIN
    UPDATE keyword_patterns k
    SET accuracy = CASE 
        WHEN k.times_matched > 0 THEN (k.times_correct::FLOAT / k.times_matched::FLOAT)
        ELSE 0
    END;
END;
$$ LANGUAGE plpgsql;

-- Function: Cleanup old performance data (keep last 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_performance_data()
RETURNS void AS $$
BEGIN
    DELETE FROM provider_performance 
    WHERE timestamp < NOW() - INTERVAL '30 days';
    
    DELETE FROM daily_quota_usage
    WHERE date < CURRENT_DATE - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════════
-- SCHEMA COMPLETE
-- ═══════════════════════════════════════════════════════════════
