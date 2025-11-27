from django.core.management.base import BaseCommand
from django.utils.text import slugify
from dreambooks.models import Genre

GENRES = [
    # Broad fiction categories
    "Fantasy", "High Fantasy", "Epic Fantasy", "Urban Fantasy", "Dark Fantasy",
    "Sword and Sorcery", "Portal Fantasy", "Fairy Tale", "Arthurian", "Mythic",
    "Science Fiction", "Hard Science Fiction", "Soft Science Fiction", "Space Opera",
    "Cyberpunk", "Steampunk", "Time Travel", "Post-Apocalyptic", "Dystopian",
    "Military Science Fiction", "Alternate History", "Speculative Fiction",

    # Romance & subgenres
    "Romance", "Contemporary Romance", "Historical Romance", "Paranormal Romance",
    "Romantic Suspense", "Erotic Romance", "LGBTQ+ Romance", "Regency Romance",
    "Young Adult Romance",

    # Mystery / Thriller
    "Mystery", "Detective", "Cozy Mystery", "Noir", "Crime Fiction",
    "Police Procedural", "Private Investigator", "Legal Thriller", "Psychological Thriller",
    "Spy / Espionage", "Suspense", "Adventure Thriller",

    # Horror
    "Horror", "Gothic Horror", "Supernatural Horror", "Cosmic Horror", "Occult",
    "Psychological Horror", "Splatterpunk",

    # Historical / Literary / Contemporary
    "Historical Fiction", "Historical Mystery", "Literary Fiction", "Contemporary Fiction",
    "Women's Fiction", "Family Saga", "Coming of Age", "Magical Realism",

    # Young readers
    "Young Adult", "Middle Grade", "Children's", "Picture Book", "Early Reader",
    "Chapter Book",

    # Non‑fiction
    "Nonfiction", "Biography", "Memoir", "True Crime", "History", "Science",
    "Travel", "Philosophy", "Religion & Spirituality", "Politics", "Business",
    "Self-Help", "Essays", "Art & Photography", "Cookbook", "Health & Fitness",
    "Reference", "Education", "Parenting", "Sports",

    # Other forms/styles
    "Poetry", "Drama", "Satire", "Humor", "Classic", "Short Stories", "Anthology",
    "Graphic Novel", "Comics", "Fanfiction", "Fiction-in-verse",

    # Niche / tropes / settings (useful for tagging)
    "Slice of Life", "Harem", "Tragedy", "Redemption", "Road Trip", "Heist",
    "Political", "Medical", "Workplace", "School", "Historical Fantasy",
    "Urban", "Western", "Survival", "Eco-fiction", "Climate Fiction", "Nature",
    "Mythology Retelling", "Crime Comedy", "Satirical Fiction", "Religious Fiction",

    # Inclusive / identity tags
    "LGBTQ+", "Queer Fiction", "Feminist Fiction", "BIPOC-focused",

    # Extras (fan-oriented)
    "Crossover", "Alternate Universe", "Fix-it", "Angst", "Fluff", "Humor",
]

class Command(BaseCommand):
    help = "Seed commonly used book genres into the Genre model."

    def handle(self, *args, **options):
        created = 0
        for name in GENRES:
            obj, was_created = Genre.objects.get_or_create(
                name=name,
                defaults={'slug': slugify(name)}
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Genres seeded. Created: {created}"))