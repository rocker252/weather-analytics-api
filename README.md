# Weather Analytics API

A FastAPI-based service to ingest, store, and analyze weather data from multiple stations.

Built as part of the Corteva coding challenge - this was quite a fun project to work on! The assignment covered data modeling, ingestion, analysis, and REST API development with some interesting challenges around handling large datasets and duplicate detection.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Database Management](#database-management)
- [Testing & Coverage](#testing--coverage)
- [AWS Deployment Strategy](#aws-deployment-strategy)
- [Development Notes](#development-notes)

---

## Tech Stack

- **Python 3.11** – main programming language
- **FastAPI** – web framework for building APIs
- **SQLAlchemy (Async)** – ORM for database interaction
- **SQLite** (default) – lightweight DB for local development (PostgreSQL ready for production)
- **Alembic** – database schema migrations
- **Poetry** – dependency management and virtual environment
- **Docker & Docker Compose** – containerization and orchestration
- **Pytest & pytest-asyncio** – testing and async support

### Why These Technology Choices?

I went with **FastAPI** because the automatic OpenAPI documentation generation saves tons of time, and the async support was crucial for handling the weather data ingestion efficiently. Initially considered Django REST Framework but FastAPI's performance benefits won out.

**SQLAlchemy async** was a bit of a learning curve (the session management took me several attempts to get right), but it enables truly non-blocking database operations which matters when you're processing hundreds of thousands of weather records.

**SQLite** for development keeps things simple, but the async SQLAlchemy setup makes switching to PostgreSQL in production trivial - just change the connection string.

---

## Project Structure

```
weather-analytics-api/
├── pyproject.toml              # Poetry dependencies and project config
├── poetry.lock                 # Locked dependency versions
├── Dockerfile                  # Container configuration
├── docker-compose.yml          # Multi-service orchestration
├── Makefile                    # Development commands (lifesaver!)
├── alembic.ini                 # Database migration configuration
├── alembic/                    # Database migration files
│   ├── versions/              # Generated migration scripts
│   └── env.py                 # Migration environment setup
├── scripts/
│   └── seed_db.py             # Database initialization script
├── weather_analytics_api/
│   ├── __init__.py            # Package initialization
│   ├── main.py                # Development runner
│   ├── api.py                 # FastAPI application entry point
│   ├── config.py              # Application configuration
│   ├── db.py                  # Database connection and session management
│   ├── models.py              # SQLAlchemy ORM models
│   ├── schemas.py             # Pydantic models for request/response
│   ├── auth.py                # JWT authentication utilities (optional enhancement)
│   ├── ingest.py              # Data ingestion logic (Problem 2)
│   ├── analyze.py             # Statistics calculation (Problem 3)
│   └── routers/
│       ├── auth.py            # Authentication routes
│       └── weather.py         # Weather data routes
└── tests/
    ├── conftest.py            # Pytest configuration and fixtures
    ├── test_api.py            # API endpoint tests
    ├── test_ingest.py         # Data ingestion tests
    └── test_analyze.py        # Data analysis tests
```

---

## Setup & Installation

### Prerequisites
- Python 3.9+ (I used 3.11 for development)
- Poetry (much better than pip for dependency management)
- Docker & Docker Compose (optional but recommended)

### Quick Start

#### 1. Clone the repository
```bash
git clone <repo_url>
cd weather-analytics-api
```

#### 2. Install dependencies
```bash
poetry install
```

#### 3. Initialize database
```bash
# Run migrations first
poetry run alembic upgrade head

# Then seed with weather data (this takes a few minutes)
poetry run python scripts/seed_db.py
```

#### 4. Run the application
```bash
# Development mode (with auto-reload)
poetry run uvicorn weather_analytics_api.api:app --reload

# Or using Docker (probably easier)
docker-compose up -d --build
```

#### 5. Check it out
Open [http://localhost:8000/docs](http://localhost:8000/docs) - FastAPI's auto-generated docs are pretty slick!

---

## Running the Application

### Development Mode
```bash
# Using Make (I set up these commands to save typing)
make dev

# Or the full command
poetry run uvicorn weather_analytics_api.api:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode (Docker)
```bash
# Start everything
docker-compose up -d --build

# Check logs if something goes wrong
docker-compose logs -f

# Stop when done
docker-compose down
```

### Available Make Commands
I set up these shortcuts because I got tired of typing the full commands:

```bash
make install    # Install dependencies
make dev        # Start development server
make up         # Start application with Docker
make down       # Stop Docker services
make db-seed    # Initialize and seed database
make test       # Run tests
make coverage   # Run tests with coverage report
make lint       # Run code linting
make format     # Format code (black, isort)
make clean      # Clean up cache and temp files
```

---

## API Endpoints

### Base URL
- **Local Development**: `http://localhost:8000`
- **Docker**: `http://localhost:8000`

### Available Endpoints

#### Weather Data
- **GET** `/api/weather` - Retrieve weather measurements with filtering
- **GET** `/api/weather/stats` - Retrieve weather statistics

#### Authentication (Optional Enhancement)
- **POST** `/auth/token` - Get JWT access token for testing
  
*Note: I added JWT auth as an enhancement beyond the assignment requirements. You can disable it by commenting out the auth dependency in the router.*

#### Documentation
- **GET** `/docs` - Swagger UI documentation
- **GET** `/redoc` - ReDoc documentation
- **GET** `/openapi.json` - OpenAPI specification

### Query Parameters

#### Weather Endpoint
```http
GET /api/weather?date=2024-01-01&station_id=USC00200032&page=1&limit=100
```

**Parameters:**
- `date` (optional): Filter by specific date (YYYY-MM-DD format)
- `station_id` (optional): Filter by weather station ID
- `page` (optional): Page number for pagination (default: 1)
- `limit` (optional): Number of records per page (default: 100, max: 1000)

#### Stats Endpoint
```http
GET /api/weather/stats?year=2024&station_id=USC00200032&page=1&limit=100
```

**Parameters:**
- `year` (optional): Filter by specific year
- `station_id` (optional): Filter by weather station ID
- `page` (optional): Page number for pagination (default: 1)
- `limit` (optional): Number of records per page (default: 100, max: 1000)

### Response Format

The API returns paginated JSON responses. Here's what they look like:

#### Weather Data Response
```json
{
  "data": [
    {
      "station_id": "USC00200032",
      "date": "1985-01-01",
      "max_temp": 5.6,
      "min_temp": -2.8,
      "precipitation": 0.0
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 100,
    "total": 250000,
    "pages": 2500
  }
}
```

#### Statistics Response
```json
{
  "data": [
    {
      "station_id": "USC00200032",
      "year": 1985,
      "avg_max_temp": 15.2,
      "avg_min_temp": 3.4,
      "total_precipitation": 123.5
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 100,
    "total": 150,
    "pages": 2
  }
}
```

---

## Database Management

### Data Models

I kept the models pretty straightforward to match the assignment requirements:

#### Weather Data Model
- `station_id`: Weather station identifier (string)
- `date`: Date of measurement
- `max_temp`: Maximum temperature in degrees Celsius (converted from tenths)
- `min_temp`: Minimum temperature in degrees Celsius (converted from tenths)
- `precipitation`: Precipitation amount in centimeters (converted from tenths of mm)

#### Weather Statistics Model
- `station_id`: Weather station identifier
- `year`: Year of aggregation
- `avg_max_temp`: Average maximum temperature (°C)
- `avg_min_temp`: Average minimum temperature (°C)
- `total_precipitation`: Total precipitation (cm)

*Note: I added unique constraints on (station_id, date) and (station_id, year) to handle the duplicate detection requirement.*

### Migrations
```bash
# Create new migration after model changes
poetry run alembic revision --autogenerate -m "Description of changes"

# Apply migrations
poetry run alembic upgrade head

# Rollback if needed
poetry run alembic downgrade -1
```

### Data Ingestion
```bash
# Ingest weather data (handles duplicates gracefully)
poetry run python -m weather_analytics_api.ingest

# Calculate statistics (can be run multiple times safely)
poetry run python -m weather_analytics_api.analyze
```

**Key Features:**
- Automatic data download from GitHub if local files not found
- Duplicate detection using database constraints and upserts
- Comprehensive logging with start/end times and record counts
- Error recovery for malformed data lines
- Progress tracking for long operations

*I spent quite a bit of time getting the duplicate detection right - originally tried to catch IntegrityError but learned that doesn't work with async sessions the way I expected.*

### Manual Data Processing

**For testing individual components:**

```bash
# Run data ingestion only (Problem 2)
poetry run python -m weather_analytics_api.ingest

# Run statistics calculation only (Problem 3)  
poetry run python -m weather_analytics_api.analyze

# Custom data directory
poetry run python -m weather_analytics_api.ingest /path/to/custom/data

# Check logs for start/end times and record counts
# Both commands can be run multiple times safely
```

**What these commands do:**
- `ingest`: Downloads weather data (if needed) and loads into database with duplicate detection
- `analyze`: Calculates yearly statistics per weather station, ignoring missing values

This allows reviewers to verify that Problems 2 and 3 work correctly as standalone components.

---

## Testing & Coverage

### Running Tests
```bash
# Run all tests
make test

# Run specific test file
poetry run pytest tests/test_api.py

# Run with verbose output to see what's happening
poetry run pytest -v
```

### Coverage Reports
```bash
# Generate coverage report
make coverage

# View HTML coverage report (opens in browser)
open htmlcov/index.html
```

*Current test coverage is pretty good for the core functionality, though I could add more edge case testing for malformed data scenarios.*

---

## AWS Deployment Strategy

*This is the extra credit section - here's how I'd actually deploy this thing to production.*

### Architecture Overview

I designed this with real-world scalability and cost-effectiveness in mind. The key insight is separating the real-time API from the batch processing workloads.

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Internet      │    │   Application    │    │    Database     │
│                 │    │                  │    │                 │
│ Route 53 ────── │ ── │ ALB ──── ECS     │ ── │ RDS PostgreSQL  │
│ CloudFront      │    │         Fargate  │    │ (Multi-AZ)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌──────────────────┐
                       │   Batch Jobs     │
                       │                  │
                       │ EventBridge ──── │
                       │ Lambda/ECS       │
                       └──────────────────┘
```

### 1. API Deployment - Amazon ECS with Fargate

I'd go with **ECS Fargate** as the primary deployment target. Here's why:

**Configuration I'd use:**
```yaml
Service: weather-analytics-api
- Cluster: weather-cluster
- Launch Type: Fargate
- CPU: 512 vCPU (0.5 vCPU) - probably enough to start
- Memory: 1024 MiB (1 GB)
- Desired Count: 2 (minimum for HA)
- Auto Scaling: Target 70% CPU utilization
- Health Check: /health endpoint (need to add this)
```

**Why Fargate over EC2:**
- No server management (huge operational win)
- Automatic scaling without provisioning
- Pay only for what you use
- Better security isolation

**Alternative consideration:** Lambda + API Gateway could work for this workload and be cheaper at low traffic, but FastAPI has some cold start overhead that makes me lean toward containers.

### 2. Database Strategy - Amazon RDS PostgreSQL

**Production configuration:**
```yaml
Engine: PostgreSQL 15
Instance Class: db.t3.micro (development) / db.t3.small (production)
Storage: 20 GB General Purpose SSD (can grow as needed)
Multi-AZ: Yes (production only - costs 2x but worth it)
Backup Retention: 7 days
Encryption: At rest with KMS
```

**Security approach:**
- VPC deployment in private subnets only
- Security groups allowing access only from ECS tasks
- Secrets Manager for database credentials
- SSL/TLS enforced for all connections

*I initially considered DynamoDB but the relational queries for time-series data work better with SQL, and PostgreSQL handles the data volumes just fine.*

### 3. Scheduled Data Ingestion

This was the trickiest part to design. Two viable approaches:

#### EventBridge + Lambda (My preferred approach)
```yaml
Schedule: "cron(0 6 * * ? *)"  # Daily at 6 AM UTC
Lambda Configuration:
- Runtime: Python 3.11
- Memory: 1024 MB (might need more for large files)
- Timeout: 15 minutes
- VPC: Same as RDS for database access
```

**Pros:** Serverless, cheap, auto-scales
**Cons:** 15-minute timeout limit (though probably sufficient)

#### ECS Scheduled Tasks (Backup plan)
```yaml
Schedule: "cron(0 6 * * ? *)"
Task Definition: weather-ingest-task
CPU: 1024 vCPU
Memory: 2048 MiB
```

**Pros:** No timeout limits, can reuse container images
**Cons:** More expensive, slightly more complex

### 4. Infrastructure as Code

I'd use **AWS CDK** with Python to keep everything in the same language:

```python
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_ecs as ecs,
    RemovalPolicy
)
from constructs import Construct

class WeatherApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        # VPC with public/private subnets across 2 AZs
        vpc = ec2.Vpc(
            self, "WeatherVpc",
            max_azs=2,
            nat_gateways=1  # Cost optimization - 1 NAT instead of 2
        )
        
        # RDS PostgreSQL in private subnets
        database = rds.DatabaseInstance(
            self, "WeatherDB",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_15
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3,
                ec2.InstanceSize.MICRO
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            removal_policy=RemovalPolicy.SNAPSHOT  # Safety first
        )
        
        # ECS Cluster
        cluster = ecs.Cluster(
            self, "WeatherCluster",
            vpc=vpc,
            container_insights=True
        )
        
        # ECS Service setup would go here...
```

### 5. CI/CD Pipeline

**GitHub Actions** for deployment automation:

```yaml
name: Deploy to AWS
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          poetry install
          poetry run pytest
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build and push Docker image
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
          docker build -t weather-analytics-api .
          docker push $ECR_REGISTRY/weather-analytics-api:latest
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster weather-cluster --service weather-api --force-new-deployment
```

### 6. Monitoring and Observability

**CloudWatch setup I'd implement:**
- API response times and error rates
- Database connection pool metrics
- Memory and CPU usage alerts
- Ingestion job success/failure notifications

**Key alarms:**
- API latency > 2 seconds
- Error rate > 5%
- Database CPU > 80%
- Failed ingestion jobs

### 7. Cost Analysis

**Estimated monthly costs (us-east-1):**
```
RDS db.t3.micro (Multi-AZ):     ~$25/month
ECS Fargate (2 tasks, 24/7):    ~$35/month
Application Load Balancer:      ~$22/month
NAT Gateway:                    ~$32/month
Lambda (daily ingestion):       ~$1/month
CloudWatch Logs:                ~$5/month
Data Transfer:                  ~$10/month
--------------------------------
Total:                          ~$130/month
```

**Cost optimization strategies:**
- Use Spot instances for batch processing
- Implement auto-scaling to scale down during low traffic
- Set CloudWatch log retention policies
- Consider Reserved Instances after traffic patterns are established

### 8. Security Considerations

**Network security:**
- VPC with private subnets for all compute and data
- Security groups with least-privilege access
- WAF on the ALB for common attack protection

**Data security:**
- Encryption at rest (RDS, EBS volumes)
- Encryption in transit (SSL/TLS everywhere)
- Secrets Manager for database credentials
- IAM roles with minimal required permissions

### 9. Deployment Commands

**Initial setup workflow:**
```bash
# 1. Build and push container
aws ecr create-repository --repository-name weather-analytics-api
docker build -t weather-analytics-api .
docker push $ECR_REGISTRY/weather-analytics-api:latest

# 2. Deploy infrastructure
cdk deploy WeatherApiStack

# 3. Run initial database setup
aws ecs run-task --cluster weather-cluster --task-definition migration-task
```

**Ongoing deployments:**
```bash
# Deploy new version
docker build -t weather-analytics-api:v2.0 .
docker push $ECR_REGISTRY/weather-analytics-api:v2.0
aws ecs update-service --cluster weather-cluster --service weather-api --force-new-deployment
```

**Disaster recovery:**
- Cross-region RDS backup replication
- Route 53 health checks for automatic failover
- Infrastructure code in version control for quick rebuild

---

## Development Notes

### What Went Well
- FastAPI's automatic documentation saved tons of time
- SQLAlchemy's async support performed great with large datasets
- Docker setup made deployment testing much easier
- The unique constraint approach for duplicate detection worked perfectly

### Challenges I Ran Into
- **Async session management**: Took me several attempts to get the session lifecycle right, especially with the ingestion process
- **Precipitation conversion**: Initially did the conversion wrong (divided by 10 twice) and had to debug why my API was returning tiny precipitation values
- **Duplicate detection**: First tried catching IntegrityError at add() time, but learned it only occurs at commit() time with async sessions
- **Pydantic v2 migration**: Had to update from v1 validator syntax to v2 field_validator - the migration guide was helpful

### Current Limitations & TODOs
- [ ] Add rate limiting to the API endpoints
- [ ] Implement more granular error handling for edge cases
- [ ] Add health check endpoint for load balancer monitoring
- [ ] Consider adding caching for frequently accessed statistics
- [ ] Could optimize the statistics calculation for very large datasets
- [ ] Add more comprehensive integration tests for the ingestion process

### Things I'd Do Differently Next Time
- Start with proper async session patterns from the beginning instead of retrofitting
- Set up proper logging configuration earlier in development
- Consider using a task queue (Celery) for the data processing if this scaled much larger
- Maybe implement the statistics calculation as incremental updates rather than full recalculation

### References & Learning
- FastAPI async patterns from the official documentation
- SQLAlchemy async session management from Real Python tutorials
- AWS ECS deployment strategies from AWS Well-Architected Framework docs
- Alembic migration patterns from SQLAlchemy documentation
- Used GitHub Copilot for some boilerplate code generation and documentation formatting

---

This was a really interesting project to work on - hit a good balance of data engineering, API development, and system design considerations. The duplicate detection requirement really made me think through the edge cases carefully!