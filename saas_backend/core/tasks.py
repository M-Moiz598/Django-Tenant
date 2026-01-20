from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_task_reminder_email(task_id, tenant_schema):
    """
    Send reminder email for a task.
    Must handle tenant context for multi-tenancy.
    """
    from django.db import connection
    from django_tenants.utils import schema_context
    from .models import Task

    try:
        with schema_context(tenant_schema):
            task = Task.objects.select_related('assigned_to', 'project').get(id=task_id)

            if task.assigned_to and task.assigned_to.email:
                subject = f'Task Reminder: {task.title}'
                message = f"""
                Hi {task.assigned_to.get_full_name() or task.assigned_to.username},

                This is a reminder about your task:

                Project: {task.project.name}
                Task: {task.title}
                Priority: {task.get_priority_display()}
                Due Date: {task.due_date}

                Please complete this task at your earliest convenience.

                Best regards,
                Your SaaS Team
                """

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [task.assigned_to.email],
                    fail_silently=False,
                )

                logger.info(f"Reminder email sent for task {task_id} in tenant {tenant_schema}")
                return f"Email sent to {task.assigned_to.email}"

    except Exception as e:
        logger.error(f"Error sending reminder for task {task_id}: {str(e)}")
        raise


@shared_task
def check_overdue_tasks():
    """
    Check for overdue tasks across all tenants and send notifications.
    This is a periodic task that runs via Celery Beat.
    """
    from tenants.models import Company
    from django_tenants.utils import schema_context
    from .models import Task

    now = timezone.now()
    total_overdue = 0

    # Iterate through all active tenants
    for tenant in Company.objects.filter(is_active=True):
        try:
            with schema_context(tenant.schema_name):
                # Find overdue tasks that are not completed
                overdue_tasks = Task.objects.filter(
                    due_date__lt=now,
                    status__in=['todo', 'in_progress', 'review']
                ).select_related('assigned_to', 'project')

                for task in overdue_tasks:
                    total_overdue += 1

                    # Send reminder email asynchronously
                    if task.assigned_to:
                        send_task_reminder_email.delay(task.id, tenant.schema_name)

                logger.info(
                    f"Found {overdue_tasks.count()} overdue tasks in tenant {tenant.schema_name}"
                )

        except Exception as e:
            logger.error(f"Error checking overdue tasks for tenant {tenant.schema_name}: {str(e)}")

    return f"Checked all tenants. Found {total_overdue} overdue tasks."


@shared_task
def generate_project_report(project_id, tenant_schema):
    """
    Generate a comprehensive project report.
    This is an example of a long-running background task.
    """
    from django_tenants.utils import schema_context
    from .models import Project, Task
    import time

    try:
        with schema_context(tenant_schema):
            project = Project.objects.prefetch_related('tasks', 'members').get(id=project_id)

            # Simulate long-running task
            time.sleep(2)

            tasks = project.tasks.all()

            report = {
                'project_name': project.name,
                'owner': project.owner.username,
                'total_members': project.members.count(),
                'total_tasks': tasks.count(),
                'completed_tasks': tasks.filter(status='done').count(),
                'pending_tasks': tasks.filter(status__in=['todo', 'in_progress']).count(),
                'overdue_tasks': tasks.filter(
                    due_date__lt=timezone.now(),
                    status__in=['todo', 'in_progress']
                ).count(),
                'tasks_by_priority': {
                    'low': tasks.filter(priority='low').count(),
                    'medium': tasks.filter(priority='medium').count(),
                    'high': tasks.filter(priority='high').count(),
                    'urgent': tasks.filter(priority='urgent').count(),
                },
                'generated_at': timezone.now().isoformat()
            }

            logger.info(f"Generated report for project {project_id} in tenant {tenant_schema}")
            return report

    except Exception as e:
        logger.error(f"Error generating report for project {project_id}: {str(e)}")
        raise


@shared_task
def cleanup_old_data(days=90):
    """
    Clean up old completed tasks across all tenants.
    Runs periodically to maintain database performance.
    """
    from tenants.models import Company
    from django_tenants.utils import schema_context
    from .models import Task
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=days)
    total_deleted = 0

    for tenant in Company.objects.filter(is_active=True):
        try:
            with schema_context(tenant.schema_name):
                # Delete completed tasks older than cutoff date
                deleted_count, _ = Task.objects.filter(
                    status='done',
                    completed_at__lt=cutoff_date
                ).delete()

                total_deleted += deleted_count

                if deleted_count > 0:
                    logger.info(
                        f"Deleted {deleted_count} old tasks from tenant {tenant.schema_name}"
                    )

        except Exception as e:
            logger.error(f"Error cleaning up data for tenant {tenant.schema_name}: {str(e)}")

    return f"Cleanup completed. Deleted {total_deleted} old tasks across all tenants."


@shared_task
def send_welcome_email(user_id, tenant_schema):
    """
    Send welcome email to new user.
    """
    from django_tenants.utils import schema_context
    from django.contrib.auth.models import User

    try:
        with schema_context(tenant_schema):
            user = User.objects.get(id=user_id)

            subject = 'Welcome to Our SaaS Platform!'
            message = f"""
            Hi {user.get_full_name() or user.username},

            Welcome to our platform! Your account has been successfully created.

            You can now start collaborating with your team, managing projects, and tracking tasks.

            If you have any questions, please don't hesitate to reach out to our support team.

            Best regards,
            The Team
            """

            if user.email:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )

                logger.info(f"Welcome email sent to user {user_id} in tenant {tenant_schema}")
                return f"Welcome email sent to {user.email}"

    except Exception as e:
        logger.error(f"Error sending welcome email to user {user_id}: {str(e)}")
        raise