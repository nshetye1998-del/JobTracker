#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# DEVELOPMENT DEPLOYMENT SCRIPT
# ═══════════════════════════════════════════════════════════════
# This script:
# 1. Creates development directories (can be cleared anytime)
# 2. Optionally clears dev database
# 3. Builds and starts development environment
# 4. Initializes database schema
# ═══════════════════════════════════════════════════════════════

set -e  # Exit on error

echo "═══════════════════════════════════════════════════════════════"
echo "🔧 JOB TRACKER - DEVELOPMENT DEPLOYMENT"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Navigate to deploy directory
cd "$(dirname "$0")"

echo "Step 1: Managing development directories..."
echo "────────────────────────────────────────────────────────────────"

# Ask if user wants to clear dev database
echo ""
read -p "Clear development database? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Clearing development database..."
    docker-compose -f docker-compose.dev.yml down -v
    echo "✓ Development data cleared"
else
    echo "ℹ️  Preserving existing development data"
    docker-compose -f docker-compose.dev.yml down || true
fi

echo ""
echo "Step 2: Building services with latest code..."
echo "────────────────────────────────────────────────────────────────"
docker-compose -f docker-compose.dev.yml build
echo "✓ Services built"

echo ""
echo "Step 3: Starting development services..."
echo "────────────────────────────────────────────────────────────────"
docker-compose -f docker-compose.dev.yml up -d
echo "✓ Services starting..."

echo ""
echo "Step 4: Waiting for PostgreSQL to be ready..."
echo "────────────────────────────────────────────────────────────────"
sleep 10

# Wait for PostgreSQL
max_attempts=30
attempt=0
while ! docker-compose -f docker-compose.dev.yml exec -T postgres pg_isready -U admin > /dev/null 2>&1; do
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
echo "Step 5: Initializing database schema..."
echo "────────────────────────────────────────────────────────────────"

# Always apply schema in dev (idempotent)
echo "  Applying schema.sql..."
docker-compose -f docker-compose.dev.yml exec -T postgres psql -U admin -d job_tracker_dev < ../services/common/schema.sql
echo "✓ Database schema initialized"

echo ""
echo "Step 6: Checking service health..."
echo "────────────────────────────────────────────────────────────────"
sleep 5

# Check running containers
running=$(docker-compose -f docker-compose.dev.yml ps --services --filter "status=running" | wc -l)
total=$(docker-compose -f docker-compose.dev.yml ps --services | wc -l)

echo "  Services running: $running/$total"

if [ $running -lt $total ]; then
    echo "⚠️  Some services may not be running. Check logs:"
    echo "     docker-compose -f docker-compose.dev.yml logs"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ DEVELOPMENT ENVIRONMENT READY!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📊 Dashboard:       http://localhost:3301"
echo "📈 Grafana:         http://localhost:3002 (admin/admin)"
echo "⚙️  Prometheus:      http://localhost:9091"
echo "🔍 Kafka:           localhost:9093"
echo "💾 PostgreSQL:      localhost:5433"
echo ""
echo "📝 Useful commands:"
echo "   Logs (all):      docker-compose -f docker-compose.dev.yml logs -f"
echo "   Logs (service):  docker-compose -f docker-compose.dev.yml logs -f <service>"
echo "   Status:          docker-compose -f docker-compose.dev.yml ps"
echo "   Stop:            docker-compose -f docker-compose.dev.yml down"
echo "   Clear data:      docker-compose -f docker-compose.dev.yml down -v"
echo "   Restart:         docker-compose -f docker-compose.dev.yml restart <service>"
echo ""
echo "💡 Development runs on different ports to avoid conflicts with production"
echo "💡 Production data is completely separate and untouched"
echo ""
echo "═══════════════════════════════════════════════════════════════"
