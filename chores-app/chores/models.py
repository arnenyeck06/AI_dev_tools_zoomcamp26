from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


class Household(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Membership(models.Model):
    class Role(models.TextChoices):
        PARENT = 'parent', 'Parent'
        MEMBER = 'member', 'Member'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # A user belongs to a given household at most once.
            models.UniqueConstraint(
                fields=['user', 'household'],
                name='unique_user_per_household',
            ),
            # At most one parent per household (v1). "Exactly one" is enforced
            # by the create-household / member-management flows (task #2).
            models.UniqueConstraint(
                fields=['household'],
                condition=Q(role='parent'),
                name='one_parent_per_household',
            ),
        ]

    def __str__(self):
        return f'{self.user} in {self.household} ({self.role})'


class Chore(models.Model):
    class Type(models.TextChoices):
        RECURRING = 'recurring', 'Recurring (weekly)'
        ONE_OFF = 'one_off', 'One-off'

    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name='chores',
    )
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    chore_type = models.CharField(max_length=10, choices=Type.choices)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ChoreAssignment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        DONE = 'done', 'Done'

    chore = models.ForeignKey(
        Chore,
        on_delete=models.CASCADE,
        related_name='assignments',
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chore_assignments',
    )
    due_date = models.DateField()
    # First day of the ISO week this assignment covers; null for one-off chores.
    week_start = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # One assignment per recurring chore per week.
            models.UniqueConstraint(
                fields=['chore', 'week_start'],
                condition=Q(week_start__isnull=False),
                name='unique_chore_assignment_per_week',
            ),
        ]

    def __str__(self):
        return f'{self.chore} -> {self.assignee} ({self.status})'


class Grade(models.Model):
    assignment = models.OneToOneField(
        ChoreAssignment,
        on_delete=models.CASCADE,
        related_name='grade',
    )
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='grades_given',
    )
    graded_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(score__gte=1) & Q(score__lte=5),
                name='grade_score_between_1_and_5',
            ),
        ]

    def __str__(self):
        return f'{self.assignment}: {self.score}/5'
