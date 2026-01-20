from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import connection
from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create a UserProfile when a User is created.
    Only for tenant schemas, not for public schema.
    """
    if created:
        # Check if we're in a tenant schema (not public)
        schema_name = connection.schema_name
        if schema_name != 'public':
            UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the UserProfile whenever the User is saved.
    Only for tenant schemas, not for public schema.
    """
    schema_name = connection.schema_name
    if schema_name != 'public' and hasattr(instance, 'profile'):
        instance.profile.save()