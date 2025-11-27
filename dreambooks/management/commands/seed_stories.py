from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
import random

from dreambooks.models import Story, Chapter

fake = Faker()
User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with random stories and chapters."

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of stories to create'
        )
        parser.add_argument(
            '--chapters',
            type=int,
            default=3,
            help='Number of chapters per story'
        )

    def handle(self, *args, **options):
        count = options['count']
        chapters_count = options['chapters']

        # 1️⃣ Create or get a default author
        author, created = User.objects.get_or_create(
            username="seed_user",
            defaults={"email": "seed@example.com"}
        )
        if created:
            author.set_password("password123")
            author.save()
            self.stdout.write(self.style.SUCCESS("Created default author 'seed_user'"))

        # 2️⃣ Create stories
        for _ in range(count):
            story = Story.objects.create(
                title=fake.sentence(nb_words=5),
                description=fake.paragraph(nb_sentences=3),
                author=author,  # 🔥 assign author
            )

            # 3️⃣ Create chapters for each story
            for i in range(1, chapters_count + 1):
                Chapter.objects.create(
                    story=story,
                    title=f"Chapter {i}",
                    content=fake.paragraph(nb_sentences=10),
                    order=i
                )

            self.stdout.write(
                self.style.SUCCESS(f"Created story: {story.title} with {chapters_count} chapters")
            )

        self.stdout.write(self.style.SUCCESS("Seeding complete!"))
