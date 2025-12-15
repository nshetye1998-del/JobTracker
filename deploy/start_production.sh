#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# PRODUCTION DEPLOYMENT SCRIPT
# ═══════════════════════════════════════════════════════════════
# This script:
# 1. Creates persistent production directories
# 2. Stops existing containers (preserves data)
# 3. Builds services with latest code
# 4. Initializes production database schema
# 5. Starts all services
# ═══════════════════════════════════════════════════════════════

set -e  # Exit on error

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 JOB TRACKER - PRODUCTION DEPLOYMENT"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check if running as root for directory creation
if [[ $EUID -eq 0 ]]; then
   echo "⚠️  This script should NOT be run as root"
   echo "   Run: sudo mkdir -p /var/lib/job-tracker-production first"
   echo "   Then: sudo chown -R \$(whoami):\$(whoami) /var/lib/job-tracker-production"
   echo "   Then: ./start_production.sh"
   exit 1
fi

# Navigate to deploy directory
cd "$(dirname "$0")"

echo "Step 1: Creating persistent production directories..."
echo "────────────────────────────────────────────────────────────────"

# Check if directories exist, create if not
if [ ! -d "/var/lib/job-tracker-production" ]; then
    echo "⚠️  Production directory doesn't exist. Creating..."
    sudo mkdir -p /var/lib/job-tracker-production/postgres
    sudo mkdir -p /var/lib/job-tracker-production/redis
    sudo mkdir -p /var/lib/job-tracker-production/kafka
    sudo mkdir -p /var/lib/job-tracker-production/zookeeper
    sudo mkdir -p /var/lib/job-tracker-production/minio
    sudo mkdir -p /var/lib/job-tracker-production/prometheus
    sudo mkdir -p /var/lib/job-tracker-production/grafana
    sudo chown -R $(whoami):$(whoami) /var/lib/job-tracker-production
    echo "✓ Production directories created"
else
    echo "✓ Production directories exist"
fi

# Check disk space
available_space=$(df -h /var/lib/job-tracker-production | awk 'NR==2 {print $4}')
echo "✓ Available disk space: $available_space"

echo ""
echo "Step 2: Stopping existing containers (data preserved)..."
echo "────────────────────────────────────────────────────────────────"
docker-compose -f docker-compose.prod.yml down || true
echo "✓ Containers stopped"

echo ""
echo "Step 3: Building services with latest code..."
echo "────────────────────────────────────────────────────────────────"
docker-compose -f docker-compose.prod.yml build --no-cache
echo "✓ Services built"

echo ""
echo "Step 4: Starting production services..."
echo "────────────────────────────────────────────────────────────────"
docker-compose -f docker-compose.prod.yml up -d
echo "✓ Services starting..."

echo ""
echo "Step 5: Waiting for PostgreSQL to be ready..."
echo "────────────────────────────────────────────────────────────────"
sleep 10

# Wait for PostgreSQL
max_attempts=30
attempt=0
while ! docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U admin > /dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ $attempt -gt $max_attempts ]; then
        echo "❌ PostgreSQL failed to start after ${max_attempts} attempts"
        exit 1
    fi
    echo "  Waiting for PostgreSQL... (attempt $attempt/$max_attempts)"
    sleep 2
done
echo "✓ PostgreSQL ready"

echo ""
echo "Step 6: Initializing database schema..."
echo "────────────────────────────────────────────────────────────────"

# Check if schema already initialized
schema_exists=$(docker-compose -f docker-compose.prod.yml exec -T postgres psql -U admin -d job_tracker_prod -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'processed_emails');" 2>/dev/null || echo "f")

if [ "$schema_exists" = "t" ]; then
    echo "ℹ️  Database schema already exists (skipping initialization)"
else
    echo "  Applying schema.sql..."
    docker-compose -f docker-compose.prod.yml exec -T postgres psql -U admin -d job_tracker_prod < ../services/common/schema.sql
    echo "✓ Database schema initialized"
fi

echo ""
echo "Step 7: Checking service health..."
echo "────────────────────────────────────────────────────────────────"
sleep 5

# Check running containers
running=$(docker-compose -f docker-compose.prod.yml ps --services --filter "status=running" | wc -l)
total=$(docker-compose -f docker-compose.prod.yml ps --services | wc -l)

echo "  Services running: $running/$total"

if [ $running -lt $total ]; then
    echo "⚠️  Some services may not be running. Check logs:"
    echo "     docker-compose -f docker-compose.prod.yml logs"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ PRODUCTION DEPLOYMENT COMPLETE!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📊 Dashboard:       http://localhost:3300"
echo "📈 Grafana:         http://localhost:3001 (admin/admin)"
echo "⚙️  Prometheus:      http://localhost:9090"
echo "🔍 Kafka:           localhost:9092"
echo "💾 PostgreSQL:      localhost:5432"
echo ""
echo "📝 Useful commands:"
echo "   Logs (all):      docker-compose -f docker-compose.prod.yml logs -f"
echo "   Logs (service):  docker-compose -f docker-compose.prod.yml logs -f <service>"
echo "   Status:          docker-compose -f docker-compose.prod.yml ps"
echo "   Stop:            docker-compose -f docker-compose.prod.yml down"
echo "   Restart:         docker-compose -f docker-compose.prod.yml restart <service>"
echo ""
echo "⚠️  CRITICAL: Production data in /var/lib/job-tracker-production"
echo "   NEVER run: docker-compose down -v (destroys all data!)"
echo ""
echo "🧪 Run tests:       cd .. && python3 test_system.py"
echo "═══════════════════════════════════════════════════════════════"
