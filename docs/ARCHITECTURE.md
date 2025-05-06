# Cloud Architecture Documentation

This document details the AWS infrastructure powering our geospatial data analysis platform.

![AWS Infrastructure Architecture](arch_diag.png)

## Request Flow

### Public Access

External requests first hit CloudFront, which serves the React application from S3. The application then makes API calls through the Application Load Balancer (ALB) in the public subnet, which routes requests to the appropriate ECS service.

### API Processing

The ALB forwards requests to ECS tasks running in private subnets. These tasks:

1. Check Redis cache for existing responses
2. On cache miss, query RDS PostgreSQL
3. Cache the response in Redis
4. Return data to the client

## Data Pipeline

### Data Collection

1. EventBridge triggers nightly ECS tasks
2. Tasks download Census data (TIGER/Line + QuickFacts)
3. Raw data is stored in versioned S3 buckets
4. Success/failure notifications via CloudWatch

### Data Processing

1. ETL tasks process raw S3 data
2. Shapefiles are loaded into PostGIS
3. Demographic data is normalized and linked
4. Spatial indices are built for query optimization

## High Availability

### Database Layer

- RDS runs in Multi-AZ configuration
- Redis cluster provides replica for failover
- Both systems auto-recover from failures

### Application Layer

- Auto-scaling ECS tasks based on load
- ECS tasks spread across availability zones
- ALB health checks ensure service availability
- Failed tasks are automatically replaced

## Performance Optimization

### Caching Strategy

1. CloudFront caches static assets
2. Redis caches API responses:
   - Vector tiles for map display
   - Demographic data queries
   - Spatial search results (short-lived)

### Query Optimization

1. PostGIS spatial indices for geographic queries
2. Connection pooling for database access
3. Read-through caching with TTL

## Security Implementation

### Network Security

1. Public services in public subnets
2. Application components in private subnets
3. NAT Gateway for outbound traffic
4. Security groups restrict access between services

### Data Security

1. S3 buckets use server-side encryption
2. RDS and Redis encrypt data at rest
3. TLS for all service communication
4. IAM roles enforce least privilege access

## Monitoring and Operations

CloudWatch aggregates operational data:

1. Container metrics from ECS
2. Database performance from RDS
3. Cache statistics from Redis
4. ALB access logs for API requests
