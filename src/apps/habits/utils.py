from django.db.models import TextChoices, Q
from django.utils import timezone

from datetime import timedelta


class HabitPlanStatus(TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    ENDED = 'ENDED', 'Ended'
    UPCOMING = 'UPCOMING', 'Upcoming'

    @property
    def badge_class(self):
        return {
            self.UPCOMING: "amount-badge--info",
            self.ACTIVE: "amount-badge--success",
            self.ENDED: "amount-badge--muted",
        }[self]

    @property
    def query(self):
        """Returns the database query conditions for this specific status."""
        today = timezone.localdate()

        if self == self.ACTIVE:
            return Q(start_date__lte=today) & (
                    Q(end_date__isnull=True) | Q(end_date__gte=today)
            )
        elif self == self.UPCOMING:
            return Q(start_date__gt=today)
        elif self == self.ENDED:
            return Q(end_date__lt=today)

        return Q()


def dates_between(start_date, end_date):
    return (
        start_date + timedelta(days=offset)
        for offset in range((end_date - start_date).days + 1)
    )