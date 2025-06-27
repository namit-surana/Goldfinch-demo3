# Database Setup Guide for Goldfinch Research API

This guide will help you set up PostgreSQL on AWS RDS and integrate it with your EC2-hosted Python application.

## 🚀 Phase 1: AWS RDS PostgreSQL Setup

### Step 1: Create RDS Instance

1. **Go to AWS RDS Console**
   - Navigate to https://console.aws.amazon.com/rds/
   - Click "Create database"

2. **Choose Database Settings**
   - **Engine type**: PostgreSQL
   - **Version**: 15.x (latest stable)
   - **Template**: Free tier (development) or Production

3. **Configure Instance**
   - **DB instance identifier**: `goldfinch-research-db`
   - **Master username**: `admin` (or your choice)
   - **Master password**: Generate a strong password (save this!)
   - **Instance size**: 
     - Development: `db.t3.micro` (free tier)
     - Production: `db.t3.small` or larger

4. **Storage Configuration**
   - **Storage type**: General Purpose SSD (gp2)
   - **Allocated storage**: 20GB (free tier) or as needed
   - **Enable storage autoscaling**: Yes (recommended)

5. **Connectivity**
   - **VPC**: Same VPC as your EC2 instance
   - **Public access**: Yes (for development) or No (for production)
   - **VPC security group**: Create new or use existing
   - **Availability Zone**: Same as your EC2 instance
   - **Database port**: 5432 (default)

6. **Database Authentication**
   - **Database authentication options**: Password authentication

7. **Additional Configuration**
   - **Initial database name**: `goldfinch_research`
   - **Backup retention period**: 7 days
   - **Enable monitoring**: Basic monitoring

8. **Click "Create database"**

### Step 2: Configure Security Groups

1. **EC2 Security Group** (Outbound)
   - Type: PostgreSQL
   - Protocol: TCP
   - Port: 5432
   - Destination: RDS security group

2. **RDS Security Group** (Inbound)
   - Type: PostgreSQL
   - Protocol: TCP
   - Port: 5432
   - Source: EC2 security group

### Step 3: Get Connection Details

1. **Find your RDS endpoint**
   - Go to RDS Console → Databases
   - Click on your database
   - Copy the "Endpoint" (e.g., `goldfinch-research-db.abc123.us-east-1.rds.amazonaws.com`)

2. **Note your credentials**
   - Username: `admin` (or what you chose)
   - Password: (what you set)
   - Database: `goldfinch_research`

## 🛠️ Phase 2: Environment Configuration

### Step 1: Update Environment Variables

1. **Create/update your `.env` file**:
```bash
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Database Configuration
DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
DB_PORT=5432
DB_NAME=goldfinch_research
DB_USER=admin
DB_PASSWORD=your_secure_password_here

# Database Options
USE_SQLITE=false
DB_ECHO=false

# Application Settings
DEBUG=true
LOG_LEVEL=INFO
```

2. **Load environment variables on EC2**:
```bash
# Add to your ~/.bashrc or ~/.profile
export DB_HOST="your-rds-endpoint.region.rds.amazonaws.com"
export DB_PORT="5432"
export DB_NAME="goldfinch_research"
export DB_USER="admin"
export DB_PASSWORD="your_secure_password_here"
export USE_SQLITE="false"
export DB_ECHO="false"
```

## 📦 Phase 3: Install Dependencies

### Step 1: Install Python Dependencies

```bash
# On your EC2 instance
cd /path/to/Goldfinch-demo3
pip install -r requirements.txt
```

### Step 2: Install PostgreSQL Client (if needed)

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install libpq-dev python3-dev

# Amazon Linux
sudo yum install postgresql-devel python3-devel
```

## 🗄️ Phase 4: Database Initialization

### Step 1: Initialize Database

```bash
# Run the initialization script
python init_database.py
```

This will:
- Create all database tables
- Test the connection
- Optionally create sample data

### Step 2: Verify Setup

```bash
# Test database connection
python -c "
from database.connection import get_engine
from sqlalchemy import text
engine = get_engine()
with engine.connect() as conn:
    result = conn.execute(text('SELECT version();'))
    print('Database connected:', result.fetchone()[0])
"
```

## 🚀 Phase 5: Start Your Application

### Step 1: Start the API Server

```bash
# Start your FastAPI server
python start_api.py
```

### Step 2: Test the Integration

```bash
# Test the health endpoint
curl http://localhost:8000/health

# Test a research request
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{
    "research_question": "what are required certifications to export honey from India to US",
    "domain_list_metadata": []
  }'
```

## 🔍 Phase 6: Monitor and Debug

### Step 1: Check Database Logs

```bash
# View your application logs
tail -f /path/to/your/app.log

# Check for database-related print statements
grep "DATABASE" /path/to/your/app.log
```

### Step 2: Database Queries

Connect to your database to verify data:

```bash
# Connect using psql (install if needed)
psql -h your-rds-endpoint -U admin -d goldfinch_research

# Or use a GUI tool like pgAdmin
```

## 🛡️ Phase 7: Security Best Practices

### Step 1: Production Security

1. **Use IAM Authentication** (recommended for production)
2. **Enable encryption at rest**
3. **Use private subnets**
4. **Regular backups**
5. **Monitor access logs**

### Step 2: Environment Variables

```bash
# Use AWS Secrets Manager for production
aws secretsmanager create-secret \
  --name "goldfinch/database" \
  --description "Database credentials" \
  --secret-string '{"username":"admin","password":"your_password","host":"your-endpoint"}'
```

## 🔧 Troubleshooting

### Common Issues

1. **Connection Timeout**
   - Check security groups
   - Verify VPC configuration
   - Test connectivity: `telnet your-endpoint 5432`

2. **Authentication Failed**
   - Verify username/password
   - Check if database exists
   - Ensure user has proper permissions

3. **Import Errors**
   - Install missing dependencies: `pip install psycopg2-binary`
   - Check Python path
   - Verify file permissions

### Debug Commands

```bash
# Test database connection
python -c "from database.connection import get_engine; print(get_engine())"

# Check environment variables
env | grep DB_

# View database tables
python -c "
from database.models import Base
from database.connection import engine
Base.metadata.create_all(engine)
print('Tables created successfully')
"
```

## 📊 Next Steps

1. **Set up monitoring** (CloudWatch, etc.)
2. **Configure backups** (automated snapshots)
3. **Implement user authentication**
4. **Add database migrations** (Alembic)
5. **Set up read replicas** (for high availability)

## 🎯 API Endpoints

Your API now includes these database-integrated endpoints:

- `POST /research` - Research with database storage
- `GET /sessions/{session_id}/messages` - Get chat messages
- `GET /sessions/{session_id}/research-history` - Get research history
- `POST /sessions` - Create new session
- `GET /health` - Health check

All research requests and results are now automatically stored in the database with full audit trails! 