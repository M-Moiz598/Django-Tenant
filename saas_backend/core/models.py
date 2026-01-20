from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Extended user profile for tenant users.
    Each tenant has its own set of users.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    phone = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Project(models.Model):
    """
    Projects within a tenant.
    Tenant isolation is automatic via separate schemas.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')

    # Project ownership and team
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    members = models.ManyToManyField(User, related_name='projects', blank=True)

    # Dates
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Task(models.Model):
    """
    Tasks within projects.
    Automatic tenant isolation through project relationship.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'In Review'),
        ('done', 'Done'),
    ]

    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')

    # Assignment
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')

    # Dates
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project.name} - {self.title}"