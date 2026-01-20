"""
Test script to demonstrate API usage.
Run after setting up the project.

Usage:
    python test_api_requests.py
"""

import requests
import json

# Base URL - adjust based on your setup
BASE_URL = "http://localhost:8000"
PUBLIC_URL = f"{BASE_URL}/api"  # Public schema
TENANT_URL = f"{BASE_URL}/api"  # Tenant schema (will use different domain)


def print_response(title, response):
    """Helper to print API responses"""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")


def test_health_check():
    """Test health check endpoint"""
    response = requests.get(f"{PUBLIC_URL}/health/")
    print_response("Health Check", response)
    return response


def test_company_registration():
    """Test company registration"""
    data = {
        "company_name": "Test Company",
        "schema_name": "testcompany",
        "domain_url": "testcompany.localhost",
        "admin_username": "admin",
        "admin_email": "admin@testcompany.com",
        "admin_password": "SecurePass123!",
        "subscription_plan": "basic"
    }

    response = requests.post(f"{PUBLIC_URL}/register/", json=data)
    print_response("Company Registration", response)
    return response


def get_auth_token(username, password):
    """Get JWT authentication token"""
    data = {
        "username": username,
        "password": password
    }

    response = requests.post(f"{TENANT_URL}/token/", json=data)
    print_response("Get Auth Token", response)

    if response.status_code == 200:
        return response.json().get('access')
    return None


def create_project(token, project_data):
    """Create a new project"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{TENANT_URL}/projects/",
        json=project_data,
        headers=headers
    )
    print_response("Create Project", response)
    return response


def list_projects(token):
    """List all projects"""
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(f"{TENANT_URL}/projects/", headers=headers)
    print_response("List Projects", response)
    return response


def create_task(token, task_data):
    """Create a new task"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{TENANT_URL}/tasks/",
        json=task_data,
        headers=headers
    )
    print_response("Create Task", response)
    return response


def list_tasks(token, filters=None):
    """List tasks with optional filters"""
    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = f"{TENANT_URL}/tasks/"
    if filters:
        params = "&".join([f"{k}={v}" for k, v in filters.items()])
        url = f"{url}?{params}"

    response = requests.get(url, headers=headers)
    print_response("List Tasks", response)
    return response


def get_dashboard_stats(token):
    """Get dashboard statistics"""
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(f"{TENANT_URL}/dashboard/", headers=headers)
    print_response("Dashboard Statistics", response)
    return response


def register_user(token, user_data):
    """Register a new user in the tenant"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{TENANT_URL}/users/register/",
        json=user_data,
        headers=headers
    )
    print_response("Register User", response)
    return response


def run_tests():
    """Run all API tests"""
    print("\n" + "=" * 60)
    print("Starting API Tests")
    print("=" * 60)

    # Test 1: Health Check
    test_health_check()

    # Test 2: Register Company
    # Note: Comment out if company already exists
    # test_company_registration()

    # Test 3: Get Authentication Token
    token = get_auth_token("admin", "SecurePass123!")

    if not token:
        print("\n❌ Authentication failed. Cannot continue tests.")
        return

    print(f"\n✅ Authentication successful. Token: {token[:20]}...")

    # Test 4: Create Project
    project_data = {
        "name": "API Test Project",
        "description": "This project was created via API",
        "status": "active",
        "start_date": "2024-01-01"
    }
    project_response = create_project(token, project_data)

    project_id = None
    if project_response.status_code == 201:
        project_id = project_response.json().get('id')
        print(f"\n✅ Project created with ID: {project_id}")

    # Test 5: List Projects
    list_projects(token)

    # Test 6: Create Task
    if project_id:
        task_data = {
            "project": project_id,
            "title": "API Test Task",
            "description": "This task was created via API",
            "priority": "high",
            "status": "todo",
            "due_date": "2024-12-31T23:59:59Z"
        }
        create_task(token, task_data)

    # Test 7: List Tasks
    list_tasks(token)

    # Test 8: List My Tasks
    list_tasks(token, {"assigned_to": "me"})

    # Test 9: Dashboard Stats
    get_dashboard_stats(token)

    # Test 10: Register New User
    user_data = {
        "username": "testuser",
        "email": "testuser@testcompany.com",
        "password": "TestPass123!",
        "first_name": "Test",
        "last_name": "User",
        "role": "member",
        "department": "Engineering"
    }
    register_user(token, user_data)

    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_tests()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to the server.")
        print("Make sure the Django server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")