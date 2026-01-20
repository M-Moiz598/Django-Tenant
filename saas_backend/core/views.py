from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.db.models import Q

from .models import UserProfile, Project, Task
from .serializers import (
    UserSerializer, UserProfileSerializer, UserRegistrationSerializer,
    ProjectSerializer, TaskSerializer
)
from .permissions import (
    IsTenantUser, IsProjectOwnerOrMember, IsTaskProjectMember, IsAdminOrOwner
)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users within the tenant.
    Automatic tenant isolation via django-tenants.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get_queryset(self):
        """Return all user profiles in current tenant"""
        return UserProfile.objects.select_related('user').all()

    @action(detail=False, methods=['post'])
    def register(self, request):
        """Register a new user in the current tenant"""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            profile = user.profile
            return Response(
                UserProfileSerializer(profile).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        return Response(UserProfileSerializer(profile).data)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing projects within the tenant.
    Users can only see projects they own or are members of.
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get_queryset(self):
        """
        Return projects where user is owner or member.
        This enforces tenant isolation at queryset level.
        """
        user = self.request.user
        return Project.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct().prefetch_related('members', 'tasks')

    def get_permissions(self):
        """
        Use different permissions for different actions.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsProjectOwnerOrMember]
        else:
            permission_classes = [IsAuthenticated, IsTenantUser]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a member to the project"""
        project = self.get_object()

        # Only owner can add members
        if project.owner != request.user:
            return Response(
                {'error': 'Only project owner can add members'},
                status=status.HTTP_403_FORBIDDEN
            )

        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            project.members.add(user)
            return Response(
                ProjectSerializer(project, context={'request': request}).data
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Remove a member from the project"""
        project = self.get_object()

        # Only owner can remove members
        if project.owner != request.user:
            return Response(
                {'error': 'Only project owner can remove members'},
                status=status.HTTP_403_FORBIDDEN
            )

        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            project.members.remove(user)
            return Response(
                ProjectSerializer(project, context={'request': request}).data
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get project statistics"""
        project = self.get_object()
        tasks = project.tasks.all()

        stats = {
            'total_tasks': tasks.count(),
            'todo': tasks.filter(status='todo').count(),
            'in_progress': tasks.filter(status='in_progress').count(),
            'review': tasks.filter(status='review').count(),
            'done': tasks.filter(status='done').count(),
            'by_priority': {
                'low': tasks.filter(priority='low').count(),
                'medium': tasks.filter(priority='medium').count(),
                'high': tasks.filter(priority='high').count(),
                'urgent': tasks.filter(priority='urgent').count(),
            }
        }

        return Response(stats)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tasks within the tenant.
    Users can only see tasks from projects they have access to.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get_queryset(self):
        """
        Return tasks from projects user has access to.
        This enforces tenant isolation at queryset level.
        """
        user = self.request.user

        # Get accessible projects
        accessible_projects = Project.objects.filter(
            Q(owner=user) | Q(members=user)
        )

        # Filter tasks by accessible projects
        queryset = Task.objects.filter(
            project__in=accessible_projects
        ).select_related('project', 'assigned_to', 'created_by')

        # Filter by query parameters
        project_id = self.request.query_params.get('project', None)
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        assigned_to = self.request.query_params.get('assigned_to', None)
        if assigned_to:
            if assigned_to == 'me':
                queryset = queryset.filter(assigned_to=user)
            else:
                queryset = queryset.filter(assigned_to_id=assigned_to)

        return queryset

    def get_permissions(self):
        """Use different permissions for different actions"""
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsTaskProjectMember]
        else:
            permission_classes = [IsAuthenticated, IsTenantUser]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None):
        """Mark a task as complete"""
        from django.utils import timezone

        task = self.get_object()
        task.status = 'done'
        task.completed_at = timezone.now()
        task.save()

        return Response(TaskSerializer(task, context={'request': request}).data)

    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """Get tasks assigned to current user"""
        tasks = self.get_queryset().filter(assigned_to=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Get dashboard statistics for the current user.
    """
    user = request.user

    # Get accessible projects
    projects = Project.objects.filter(
        Q(owner=user) | Q(members=user)
    ).distinct()

    # Get tasks from accessible projects
    all_tasks = Task.objects.filter(project__in=projects)
    my_tasks = all_tasks.filter(assigned_to=user)

    stats = {
        'total_projects': projects.count(),
        'total_tasks': all_tasks.count(),
        'my_tasks': {
            'total': my_tasks.count(),
            'todo': my_tasks.filter(status='todo').count(),
            'in_progress': my_tasks.filter(status='in_progress').count(),
            'done': my_tasks.filter(status='done').count(),
        },
        'projects': ProjectSerializer(
            projects[:5],
            many=True,
            context={'request': request}
        ).data,
        'recent_tasks': TaskSerializer(
            my_tasks.order_by('-created_at')[:5],
            many=True,
            context={'request': request}
        ).data
    }

    return Response(stats)