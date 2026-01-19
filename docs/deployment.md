# Deployment Guide

This guide covers deploying the FastAPI REST API Starter to various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Deployment](#docker-deployment)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Cloud Platform Guides](#cloud-platform-guides)
5. [Production Checklist](#production-checklist)
6. [Monitoring & Observability](#monitoring--observability)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying, ensure you have:

- Docker and docker-compose (for containerized deployment)
- PostgreSQL 14+ database
- Redis 6+ (optional but recommended for production)
- Domain name with SSL certificate (for HTTPS)

## Docker Deployment

### Single-Server Deployment

The simplest production deployment using docker-compose.

#### 1. Prepare the Server

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install docker-compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. Clone and Configure

```bash
git clone https://github.com/Open-Starter-Kits/fastapi-api-starter.git
cd fastapi-api-starter

# Create production environment file
cat > .env.production << 'EOF'
APP_NAME=FastAPI REST API
APP_ENV=production
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://postgres:SECURE_PASSWORD@db:5432/fastapi_prod

# Redis
REDIS_URL=redis://redis:6379/0

# Security - CHANGE THESE!
JWT_SECRET_KEY=your-secure-256-bit-random-string-here
BCRYPT_ROUNDS=12

# Tokens
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# CORS (your frontend domain)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF
```

#### 3. Create Production Compose File

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    build:
      context: .
      target: production
    env_file:
      - .env.production
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 512M
    restart: always

  db:
    environment:
      POSTGRES_PASSWORD: SECURE_PASSWORD
    volumes:
      - /data/postgres:/var/lib/postgresql/data
    restart: always

  redis:
    command: redis-server --appendonly yes --requirepass REDIS_PASSWORD
    volumes:
      - /data/redis:/data
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - api
    restart: always
```

#### 4. Deploy

```bash
# Start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f api

# Check health
curl http://localhost:8000/api/v1/health
```

### Building Optimized Images

```bash
# Build production image
docker build --target production -t fastapi-api:latest .

# Build with specific version
docker build --target production -t fastapi-api:1.0.0 .

# Push to registry
docker tag fastapi-api:1.0.0 your-registry.com/fastapi-api:1.0.0
docker push your-registry.com/fastapi-api:1.0.0
```

## Kubernetes Deployment

### Basic Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-api
  labels:
    app: fastapi-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-api
  template:
    metadata:
      labels:
        app: fastapi-api
    spec:
      containers:
      - name: api
        image: your-registry.com/fastapi-api:1.0.0
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: fastapi-secrets
        - configMapRef:
            name: fastapi-config
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/health/live
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/v1/health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: fastapi-api
spec:
  selector:
    app: fastapi-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fastapi-api
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: fastapi-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: fastapi-api
            port:
              number: 80
```

### Secrets and ConfigMaps

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: fastapi-secrets
type: Opaque
stringData:
  DATABASE_URL: postgresql+asyncpg://user:pass@postgres:5432/db
  REDIS_URL: redis://:password@redis:6379/0
  JWT_SECRET_KEY: your-secure-secret-key
---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fastapi-config
data:
  APP_ENV: production
  DEBUG: "false"
  LOG_LEVEL: INFO
  LOG_FORMAT: json
  RATE_LIMIT_ENABLED: "true"
  RATE_LIMIT_PER_MINUTE: "60"
```

### Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Cloud Platform Guides

### AWS (ECS Fargate)

1. Push image to ECR
2. Create ECS cluster
3. Define task definition with environment variables
4. Create service with ALB
5. Configure RDS PostgreSQL and ElastiCache Redis

### Google Cloud (Cloud Run)

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/fastapi-api

# Deploy
gcloud run deploy fastapi-api \
  --image gcr.io/PROJECT_ID/fastapi-api \
  --platform managed \
  --region us-central1 \
  --set-env-vars "DATABASE_URL=..." \
  --set-secrets "JWT_SECRET_KEY=jwt-secret:latest"
```

### Azure (Container Apps)

```bash
# Create container app
az containerapp create \
  --name fastapi-api \
  --resource-group mygroup \
  --environment myenv \
  --image your-registry.azurecr.io/fastapi-api:latest \
  --target-port 8000 \
  --env-vars "APP_ENV=production" \
  --secrets "jwt-secret=your-secret" \
  --secret-volume-mounts "jwt-secret=/secrets/jwt"
```

## Production Checklist

### Security

- [ ] Generate secure `JWT_SECRET_KEY` (256-bit random)
  ```bash
  openssl rand -hex 32
  ```
- [ ] Set `DEBUG=false`
- [ ] Set `APP_ENV=production`
- [ ] Configure CORS origins (specific domains, not `*`)
- [ ] Enable HTTPS (TLS termination at load balancer)
- [ ] Use strong database passwords
- [ ] Restrict database network access
- [ ] Enable Redis authentication
- [ ] Review rate limit settings

### Database

- [ ] Use managed PostgreSQL (RDS, Cloud SQL, etc.)
- [ ] Enable automated backups
- [ ] Configure connection pooling (PgBouncer if needed)
- [ ] Set appropriate `DB_POOL_SIZE` for your instance count
- [ ] Enable SSL connections

### Caching

- [ ] Use managed Redis (ElastiCache, Memorystore, etc.)
- [ ] Enable persistence (AOF recommended)
- [ ] Set memory limits and eviction policy
- [ ] Configure Redis authentication

### Infrastructure

- [ ] Set up load balancer with health checks
- [ ] Configure auto-scaling rules
- [ ] Set resource limits (CPU, memory)
- [ ] Enable container restart policies
- [ ] Set up log aggregation

### Monitoring

- [ ] Configure application logging (JSON format)
- [ ] Set up log aggregation (CloudWatch, Stackdriver, etc.)
- [ ] Configure health check endpoints in load balancer
- [ ] Set up alerting for errors and latency
- [ ] Enable distributed tracing (optional)

## Monitoring & Observability

### Health Endpoints

The API provides three health endpoints:

| Endpoint | Purpose | Use Case |
|----------|---------|----------|
| `/api/v1/health` | Basic health | Quick check |
| `/api/v1/health/live` | Liveness | K8s liveness probe |
| `/api/v1/health/ready` | Readiness | K8s readiness probe |

### Logging

Production logging outputs JSON for easy parsing:

```json
{
  "time": "2024-01-20T10:30:00Z",
  "name": "src.main",
  "level": "INFO",
  "message": "Request completed",
  "request_id": "abc123",
  "method": "GET",
  "path": "/api/v1/users/me",
  "status": 200,
  "duration_ms": 45
}
```

### Metrics (Extension Point)

To add Prometheus metrics, install `prometheus-fastapi-instrumentator`:

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### Distributed Tracing (Extension Point)

For OpenTelemetry integration:

```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

FastAPIInstrumentor.instrument_app(app)
```

## Troubleshooting

### Common Issues

#### Database Connection Refused

```
sqlalchemy.exc.OperationalError: connection refused
```

**Solutions:**
1. Check `DATABASE_URL` format
2. Verify database is running and accessible
3. Check network/firewall rules
4. Verify credentials

#### Redis Connection Failed

```
redis.exceptions.ConnectionError: Error connecting to redis
```

**Solutions:**
1. Check `REDIS_URL` format
2. Verify Redis is running
3. Check authentication (if enabled)
4. App will fall back to in-memory cache

#### JWT Decode Error

```
jose.exceptions.JWTError: Signature verification failed
```

**Solutions:**
1. Ensure `JWT_SECRET_KEY` is consistent across instances
2. Check token hasn't expired
3. Verify token was issued by this application

#### Rate Limit Issues

```
HTTP 429 Too Many Requests
```

**Solutions:**
1. Check `RATE_LIMIT_PER_MINUTE` setting
2. Implement exponential backoff in clients
3. Increase limits if appropriate for your use case

### Debug Mode

For troubleshooting in non-production:

```bash
# Enable debug mode temporarily
docker-compose exec api env DEBUG=true LOG_LEVEL=DEBUG python -m uvicorn src.main:app --reload
```

### Database Migrations

For schema changes, use Alembic:

```bash
# Generate migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Performance Issues

1. Check database query performance:
   ```python
   # Enable in development
   DB_ECHO=true
   ```

2. Monitor Redis cache hit rate

3. Review rate limiting metrics

4. Check container resource utilization:
   ```bash
   docker stats
   ```
