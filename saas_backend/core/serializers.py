from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Project, Task


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile with nested user data"""
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'role', 'phone', 'department', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserRegistrationSerializer(serializers.Serializer):
    """Serializer for registering new users within a tenant"""
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=30, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, default='member')
    phone = serializers.CharField(max_length=20, required=False)
    department = serializers.CharField(max_length=100, required=False)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists in this organization.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists in this organization.")
        return value

    def create(self, validated_data):
        # Extract profile data
        role = validated_data.pop('role', 'member')
        phone = validated_data.pop('phone', None)
        department = validated_data.pop('department', None)

        # Create user
        user = User.objects.create_user(**validated_data)

        # Create profile
        UserProfile.objects.create(
            user=user,
            role=role,
            phone=phone,
            department=department
        )

        return user


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model"""
    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    member_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        many=True,
        required=False,
        source='members'
    )
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'status', 'owner', 'members',
            'member_ids', 'start_date', 'end_date', 'task_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def get_task_count(self, obj):
        return obj.tasks.count()

    def create(self, validated_data):
        # Set owner to current user
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model"""
    assigned_to = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
        source='assigned_to'
    )
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'project', 'project_name', 'title', 'description',
            'priority', 'status', 'assigned_to', 'assigned_to_id',
            'created_by', 'due_date', 'completed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Set created_by to current user
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def validate_project(self, value):
        """Ensure user can only create tasks in projects they have access to"""
        user = self.context['request'].user
        if value.owner != user and user not in value.members.all():
            raise serializers.ValidationError(
                "You don't have permission to create tasks in this project."
            )
        return value