"""Management command to cleanup expired tokens from blacklist."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models.jwt_token_blacklist import TokenBlacklist


class Command(BaseCommand):
    """Clean up expired tokens from the blacklist."""

    help = "Delete expired tokens from blacklist to save database space"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        dry_run = options["dry_run"]

        # Get expired tokens count
        expired_tokens = TokenBlacklist.objects.filter(expires_at__lt=timezone.now())
        count = expired_tokens.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No expired tokens to clean up"))
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Would delete {count} expired token entries"
                )
            )
        else:
            TokenBlacklist.cleanup_expired()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully deleted {count} expired token entries"
                )
            )

        # Print summary
        remaining = TokenBlacklist.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Total tokens in blacklist: {remaining}"))
