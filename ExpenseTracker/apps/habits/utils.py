from django.db.models import TextChoices

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


def dates_between(start_date, end_date):
    return (
        start_date + timedelta(days=offset)
        for offset in range((end_date - start_date).days + 1)
    )