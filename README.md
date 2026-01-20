# Multi-Tenant Subscription-Based SaaS Backend

A production-ready Django backend for a multi-tenant SaaS application with organizations, users, roles, subscriptions, and asynchronous background processing.

## Features

### Core Features
- ✅ **Multi-Tenancy**: Organization-based multi-tenancy using django-tenants
- ✅ **User Management**: User profiles with role-based access control
- ✅ **Project Management**: Projects with team members and ownership
- ✅ **Task Management**: Tasks with assignments, priorities, and status tracking
- ✅ **Subscriptions**: Multiple subscription plans with usage limits
- ✅ **Background Jobs**: Celery-based asynchronous task processing
- ✅ **RESTful API**: Django REST Framework with JWT authentication
- ✅ **Docker Support**: Complete Docker setup with docker-compose

### Tenant Isolation
Tenant isolation is enforced at multiple levels:
1. **Database Level**: Separate PostgreSQL schemas per tenant
2. **Queryset Level**: Filtered querysets ensuring data separation
3. **Serializer Level**: Context-aware serializers
4. **Permission Level**: Custom permissions for tenant access

## Technology Stack

- **Django 5.0**: Web framework
- **Django REST Framework**: API development
- **django-tenants**: Multi-tenancy implementation
- **PostgreSQL**: Database with schema-based multi-tenancy
- **Celery**: Asynchronous task queue
- **Redis**: Message broker and cache
- **Docker**: Containerization

## Project Structure

```
saas_backend/
├── saas_backend/          # Main project settings
│   ├── settings.py        # Django settings with tenant configuration
│   ├── urls.py            # Tenant-specific URLs
│   ├── urls_public.py     # Public schema URLs
│   ├── celery.py          # Celery configuration
│   └── wsgi.py
├── tenants/               # Tenant/Company management (shared schema)
│   ├── models.py          # Company and Domain models
│   ├── serializers.py     # Company registration serializers
│   ├── views.py           # Company management views
│   └── admin.py
├── core/                  # Tenant-specific apps
│   ├── models.py          # UserProfile, Project, Task models
│   ├── serializers.py     # API serializers
│   ├── views.py           # API views and viewsets
│   ├── permissions.py     # Custom permissions
│   ├── tasks.py           # Celery background tasks
│   └── signals.py         # Django signals
├── docker-compose.yml     # Docker services configuration
├── Dockerfile            # Application container
├── requirements.txt      # Python dependencies
└── .env.example         # Environment variables template
```

## Installation & Setup

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+
- Redis

### Quick Start with Docker

1. **Clone the repository**
```bash
git clone <repository-url>
cd saas_backend
```

2. **Create environment file**
```bash
cp .env.example .env
```

3. **Start services with Docker Compose**
```bash
docker-compose up --build
```

4. **Run migrations (in a new terminal)**
```bash
docker-compose exec web python manage.py migrate_schemas --shared
docker-compose exec web python manage.py migrate_schemas
```

5. **Create a superuser**
```bash
docker-compose exec web python manage.py createsuperuser
```

The API will be available at `http://localhost:8000`

### Local Development Setup

1. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run migrations**
```bash
python manage.py migrate_schemas --shared
python manage.py migrate_schemas
```

5. **Create superuser**
```bash
python manage.py createsuperuser
```

6. **Run development server**
```bash
python manage.py runserver
```

7. **Start Celery worker (in separate terminal)**
```bash
celery -A saas_backend worker -l info
```

8. **Start Celery beat (in separate terminal)**
```bash
celery -A saas_backend beat -l info
```

## API Documentation

### Public Endpoints (No Authentication Required)

#### Register a New Company
```bash
POST /api/register/
{
  "company_name": "Acme Corp",
  "schema_name": "acme",
  "domain_url": "acme.localhost",
  "admin_username": "admin",
  "admin_email": "admin@acme.com",
  "admin_password": "securepassword123",
  "subscription_plan": "basic"
}
```

#### Health Check
```bash
GET /api/health/
```

### Authentication

#### Obtain JWT Token
```bash
POST /api/token/
{
  "username": "admin",
  "password": "securepassword123"
}
```

#### Refresh JWT Token
```bash
POST /api/token/refresh/
{
  "refresh": "your-refresh-token"
}
```

### Tenant-Specific Endpoints (Authentication Required)

Add `Authorization: Bearer <access_token>` header to all requests.

#### Users

```bash
# List users
GET /api/users/

# Get current user
GET /api/users/me/

# Register new user
POST /api/users/register/
{
  "username": "john",
  "email": "john@example.com",
  "password": "password123",
  "first_name": "John",
  "last_name": "Doe",
  "role": "member",
  "department": "Engineering"
}
```

#### Projects

```bash
# List projects
GET /api/projects/

# Create project
POST /api/projects/
{
  "name": "New Project",
  "description": "Project description",
  "status": "active",
  "start_date": "2024-01-01"
}

# Get project details
GET /api/projects/{id}/

# Update project
PATCH /api/projects/{id}/
{
  "status": "completed"
}

# Add member to project
POST /api/projects/{id}/add_member/
{
  "user_id": 2
}

# Remove member from project
POST /api/projects/{id}/remove_member/
{
  "user_id": 2
}

# Get project statistics
GET /api/projects/{id}/statistics/
```

#### Tasks

```bash
# List tasks
GET /api/tasks/
# Query parameters: ?project=1&status=todo&assigned_to=me

# Create task
POST /api/tasks/
{
  "project": 1,
  "title": "Implement feature",
  "description": "Task description",
  "priority": "high",
  "status": "todo",
  "assigned_to_id": 2,
  "due_date": "2024-12-31T23:59:59Z"
}

# Get task details
GET /api/tasks/{id}/

# Update task
PATCH /api/tasks/{id}/
{
  "status": "in_progress"
}

# Mark task as complete
POST /api/tasks/{id}/mark_complete/

# Get my tasks
GET /api/tasks/my_tasks/
```

#### Dashboard

```bash
# Get dashboard statistics
GET /api/dashboard/
```

## Multi-Tenancy Implementation

### How It Works

1. **Schema-based Isolation**: Each company gets its own PostgreSQL schema
2. **Domain Routing**: Requests are routed to the correct tenant based on domain/subdomain
3. **Automatic Context**: Django-tenants automatically sets the tenant context for each request
4. **Shared vs Tenant Apps**: 
   - Shared apps (tenants): Company and Domain models in public schema
   - Tenant apps (core): User, Project, Task models in tenant schemas

### Creating a New Tenant

```python
# Via API (recommended)
POST /api/register/

# Via Django shell
from tenants.models import Company, Domain

# Create company
company = Company.objects.create(
    name="New Company",
    schema_name="newcompany",
    subscription_plan="basic"
)

# Create domain
domain = Domain.objects.create(
    domain="newcompany.localhost",
    tenant=company,
    is_primary=True
)
```

### Accessing Tenant Data

```python
from django_tenants.utils import schema_context
from core.models import Project

# In a tenant context
with schema_context('acme'):
    projects = Project.objects.all()
```

## Background Tasks

### Available Tasks

1. **send_task_reminder_email**: Send email reminders for tasks
2. **check_overdue_tasks**: Periodic check for overdue tasks (runs daily)
3. **generate_project_report**: Generate comprehensive project reports
4. **cleanup_old_data**: Clean up old completed tasks (runs weekly)
5. **send_welcome_email**: Send welcome email to new users

### Running Tasks

```python
# In Django shell or views
from core.tasks import generate_project_report

# Execute asynchronously
result = generate_project_report.delay(project_id=1, tenant_schema='acme')

# Check status
result.ready()
result.get()
```

## Testing

### Running Tests
```bash
python manage.py test

# With coverage
coverage run --source='.' manage.py test
coverage report
```

### Example Test
```python
from django.test import TestCase
from django_tenants.test.cases import TenantTestCase
from core.models import Project

class ProjectTestCase(TenantTestCase):
    def test_create_project(self):
        project = Project.objects.create(
            name="Test Project",
            owner=self.user
        )
        self.assertEqual(project.name, "Test Project")
```

## Deployment

### Environment Variables

Required environment variables for production:

```bash
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=yourdomain.com,*.yourdomain.com

DATABASE_NAME=saas_db
DATABASE_USER=saas_user
DATABASE_PASSWORD=secure-password
DATABASE_HOST=db-host
DATABASE_PORT=5432

REDIS_URL=redis://redis-host:6379/0

CORS_ALLOWED_ORIGINS=https://yourdomain.com

# Email settings
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### Production Checklist

- [ ] Set DEBUG=False
- [ ] Use strong SECRET_KEY
- [ ] Configure allowed hosts
- [ ] Set up SSL/TLS certificates
- [ ] Configure email backend
- [ ] Set up database backups
- [ ] Configure logging
- [ ] Set up monitoring (Sentry, etc.)
- [ ] Configure CORS properly
- [ ] Use production-grade WSGI server (Gunicorn)
- [ ] Set up reverse proxy (Nginx)
- [ ] Configure Redis persistence
- [ ] Set up Celery monitoring

## Architecture Decisions

### Why django-tenants?

1. **True Isolation**: Each tenant gets separate database schema
2. **Performance**: Better query performance vs row-level filtering
3. **Security**: Database-level isolation prevents data leaks
4. **Scalability**: Can move schemas to different databases if needed

### Why Celery?

1. **Asynchronous Processing**: Handle long-running tasks without blocking requests
2. **Scheduled Tasks**: Built-in periodic task support
3. **Reliability**: Task retries and error handling
4. **Scalability**: Horizontal scaling of workers

## Security Considerations

1. **Tenant Isolation**: Enforced at database, queryset, and permission levels
2. **JWT Authentication**: Secure token-based authentication
3. **CORS**: Configured to allow only specific origins
4. **SQL Injection**: Protected by Django ORM
5. **XSS Protection**: Django templates auto-escape
6. **CSRF Protection**: Enabled by default
7. **Password Hashing**: PBKDF2 algorithm by default

## Performance Optimization

1. **Database Indexes**: Add indexes on frequently queried fields
2. **Query Optimization**: Use select_related() and prefetch_related()
3. **Caching**: Implement Redis caching for frequently accessed data
4. **Connection Pooling**: Use pgbouncer for database connections
5. **Celery Tasks**: Offload heavy processing to background workers

## Troubleshooting

### Common Issues

**Issue: Schema not found**
```bash
python manage.py migrate_schemas
```

**Issue: Celery tasks not executing**
```bash
# Check Celery worker is running
celery -A saas_backend inspect active

# Check Redis connection
redis-cli ping
```

**Issue: Permission denied errors**
- Ensure user is authenticated
- Check tenant context is set correctly
- Verify permissions in views

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

## License

MIT License

## Support

For issues and questions:
- Create an issue on GitHub
- Email: support@example.com

---

Built with ❤️ using Django and django-tenants