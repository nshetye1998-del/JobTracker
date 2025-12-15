-- Create admin user for job tracker services
CREATE USER admin WITH PASSWORD 'secure_password';

-- Create job tracker database
CREATE DATABASE job_tracker_prod;

-- Grant all privileges to admin
GRANT ALL PRIVILEGES ON DATABASE job_tracker_prod TO admin;

-- Connect to job_tracker_prod and set up schema
\c job_tracker_prod

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO admin;
