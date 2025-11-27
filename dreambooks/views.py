from urllib import request
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from .models import Story, Chapter, Review, Genre, ContactMessage
from django.core.paginator import Paginator
from .forms import SignUpForm, StoryForm, ReviewForm
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.db.models import Avg

def home(request):
    # Newest Update
    newest_qs = Story.objects.all().order_by('-updated_at')
    newest_paginator = Paginator(newest_qs, 4)
    newest_page_num = request.GET.get('newest_page') or 1
    newest_page_obj = newest_paginator.get_page(newest_page_num)

    # Latest stories by date
    latest_qs = Story.objects.all().order_by('-created_at') \
        .prefetch_related('genres') \
        .annotate(avg_rating=Avg('reviews__rating'))
    latest_paginator = Paginator(latest_qs, 4)
    latest_page_num = request.GET.get('latest_page') or 1
    latest_page_obj = latest_paginator.get_page(latest_page_num)

    # Top-rated stories by average rating
    rating_qs = Story.objects.all().prefetch_related('genres') \
        .annotate(avg_rating=Avg('reviews__rating')) \
        .order_by('-avg_rating', '-created_at')  # break ties by newest first
    rating_paginator = Paginator(rating_qs, 4)
    rating_page_num = request.GET.get('rating_page') or 1
    rating_page_obj = rating_paginator.get_page(rating_page_num)

    return render(request, 'dreambooks/home.html', {
        'latest_stories': latest_page_obj.object_list,
        'latest_page_obj': latest_page_obj,
        'latest_paginator': latest_paginator,
        'rating_stories': rating_page_obj.object_list,
        'rating_page_obj': rating_page_obj,
        'rating_paginator': rating_paginator,
        'newest_stories': newest_page_obj.object_list,
        'newest_page_obj': newest_page_obj,
        'newest_paginator': newest_paginator,
    })


@login_required
def chapter_create(request, slug):
    from .forms import ChapterForm  # local import to avoid circular imports
    story = get_object_or_404(Story, slug=slug)

    # Only allow story owner or staff
    is_owner = hasattr(story, 'author') and request.user == story.author
    if not (is_owner or request.user.is_staff):
        raise PermissionDenied

    if request.method == 'POST':
        form = ChapterForm(request.POST, request.FILES)
        if form.is_valid():
            chapter = form.save(commit=False)

            # attach story FK dynamically
            fk_name = None
            for f in Chapter._meta.get_fields():
                if getattr(f, 'related_model', None) is Story:
                    fk_name = f.name
                    break
            if fk_name:
                setattr(chapter, fk_name, story)
            else:
                chapter.story = story  # fallback

            # set order if present
            if 'order' in [f.name for f in Chapter._meta.get_fields()]:
                from django.db.models import Max
                current_max = Chapter.objects.filter(
                    **({fk_name: story} if fk_name else {'story': story})
                ).aggregate(Max('order')).get('order__max') or 0
                chapter.order = current_max + 1

            chapter.save()
            story.save()
            # redirect to chapter detail if that view exists, else story detail
            try:
                return redirect('chapter_detail', story.slug, chapter.pk)
            except Exception:
                return redirect('story_detail', slug=story.slug)
    else:
        form = ChapterForm()

    return render(request, 'dreambooks/chapter_create.html', {'form': form, 'story': story})


# Signup view
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'dreambooks/signup.html', {'form': form})

def story_detail(request, slug):
    story = get_object_or_404(Story, slug=slug)

    story.avg_rating = story.reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    story.real_avg_rating = story.avg_rating
    story.avg_rating = round(story.avg_rating)

    # determine related manager for chapters
    chapters_qs = None
    if hasattr(story, 'chapter_set'):
        chapters_qs = story.chapter_set.all()
    elif hasattr(story, 'chapters'):
        chapters_qs = story.chapters.all()
    else:
        try:
            chapters_qs = Chapter.objects.filter(**{
                next(f.name for f in Chapter._meta.get_fields() if getattr(f, 'related_model', None) is Story): story
            })
        except Exception:
            chapters_qs = Chapter.objects.none()

    # order chapters
    field_names = [f.name for f in Chapter._meta.get_fields()]
    if 'order' in field_names:
        chapters_qs = chapters_qs.order_by('order')
    elif 'created_at' in field_names:
        chapters_qs = chapters_qs.order_by('created_at')

    # paginate 10 chapters per page
    paginator = Paginator(chapters_qs, 10)
    page_number = request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)

    # handle review submission
    review_form = None
    if request.user.is_authenticated:
        # check if the user already posted a review for this story
        existing_review = story.reviews.filter(author=request.user).first()

        if request.method == 'POST':
            if existing_review:
                # they already reviewed → do NOT allow another
                messages.error(request, "You have already posted a review for this story.")
                return redirect('story_detail', slug=slug)

            review_form = ReviewForm(request.POST)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.story = story
                review.author = request.user
                review.save()
                messages.success(request, "Your review has been posted!")
                return redirect('story_detail', slug=slug)
        else:
            review_form = ReviewForm() if not existing_review else None


    # handle review submission
    review_form = None
    if request.user.is_authenticated:
        if request.method == 'POST':
            review_form = ReviewForm(request.POST)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.story = story
                review.author = request.user
                review.save()
                return redirect('story_detail', slug=slug)
        else:
            review_form = ReviewForm()

    reviews = story.reviews.all()

    return render(request, 'dreambooks/story_detail.html', {
        'story': story,
        'chapters': page_obj.object_list,  # only current page chapters
        'page_obj': page_obj,
        'paginator': paginator,
        'reviews': reviews,
        'review_form': review_form,
    })

def profile(request, username):
    User = get_user_model()
    profile_user = get_object_or_404(User, username=username)
    stories = Story.objects.filter(author=profile_user).order_by('-created_at')
    reviews = Review.objects.filter(author=profile_user).select_related("story").order_by("-created_at")
    return render(request, 'dreambooks/profile.html', {
        'profile_user': profile_user,
        'stories': stories,
        "reviews": reviews,
    })

@login_required
def account_update(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        user = request.user
        user.username = username
        user.email = email
        user.save()
        messages.success(request, "Account updated successfully!")
        return redirect("profile", username=user.username)
    return render(request, "dreambooks/account_update.html", {"user": request.user})

@login_required
def account_delete(request):
    if request.method == "POST":
        request.user.delete()
        messages.success(request, "Account deleted successfully!")
        return redirect("home")
    return render(request, "dreambooks/account_delete.html")

@login_required(login_url='/login/')
def story_create(request):
    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES)
        if form.is_valid():
            story = form.save(commit=False)
            story.author = request.user
            story.save()
            form.save_m2m()
            if hasattr(story, 'slug') and story.slug:
                return redirect('story_detail', slug=story.slug)
            return redirect('story_list')
    else:
        form = StoryForm()
    return render(request, 'dreambooks/story_create.html', {'form': form})


def chapter_detail(request, slug, pk):
    # ensure story exists
    story = get_object_or_404(Story, slug=slug)

    # find FK name on Chapter that points to Story (if any)
    fk_name = None
    for f in Chapter._meta.get_fields():
        if getattr(f, 'related_model', None) is Story:
            fk_name = f.name
            break

    # load chapter ensuring it belongs to the story
    if fk_name:
        chapter = get_object_or_404(Chapter, pk=pk, **{fk_name: story})
    else:
        chapter = get_object_or_404(Chapter, pk=pk)
        # extra safety: if chapter has no relation, ensure it actually belongs (best-effort)
        try:
            if getattr(chapter, 'story', None) != story:
                return get_object_or_404(Chapter, pk=0)  # force 404
        except Exception:
            pass

    # build ordered queryset for prev/next navigation
    chapters_qs = None
    if hasattr(story, 'chapter_set'):
        chapters_qs = story.chapter_set.all()
    elif hasattr(story, 'chapters'):
        chapters_qs = story.chapters.all()
    else:
        if fk_name:
            chapters_qs = Chapter.objects.filter(**{fk_name: story})
        else:
            chapters_qs = Chapter.objects.none()

    # choose ordering field
    field_names = [f.name for f in Chapter._meta.get_fields()]
    order_field = 'order' if 'order' in field_names else None
    date_field = 'created_at' if 'created_at' in field_names else None

    if order_field:
        chapters_qs = chapters_qs.order_by(order_field)
        prev_ch = chapters_qs.filter(**{f"{order_field}__lt": getattr(chapter, order_field)}).order_by(f"-{order_field}").first()
        next_ch = chapters_qs.filter(**{f"{order_field}__gt": getattr(chapter, order_field)}).order_by(order_field).first()
    elif date_field:
        chapters_qs = chapters_qs.order_by(date_field)
        prev_ch = chapters_qs.filter(**{f"{date_field}__lt": getattr(chapter, date_field)}).order_by(f"-{date_field}").first()
        next_ch = chapters_qs.filter(**{f"{date_field}__gt": getattr(chapter, date_field)}).order_by(date_field).first()
    else:
        chapters_qs = chapters_qs.order_by('pk')
        prev_ch = chapters_qs.filter(pk__lt=chapter.pk).order_by('-pk').first()
        next_ch = chapters_qs.filter(pk__gt=chapter.pk).order_by('pk').first()

    # preserve page param for back links if present
    page = request.GET.get('page')
    back_url = f"{reverse('story_detail', kwargs={'slug': story.slug})}"
    if page:
        back_url = f"{back_url}?page={page}"

    return render(request, 'dreambooks/chapter_detail.html', {
        'story': story,
        'chapter': chapter,
        'prev_chapter': prev_ch,
        'next_chapter': next_ch,
        'back_url': back_url,
    })

@login_required
def review_create(request, story_slug):
    story = get_object_or_404(Story, slug=story_slug)
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.story = story
            review.author = request.user
            review.save()
    return redirect('story_detail', slug=story_slug)

@login_required
def review_edit(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if review.author != request.user:
        return HttpResponseForbidden()
    
    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            return redirect('story_detail', slug=review.story.slug)
    else:
        form = ReviewForm(instance=review)
    
    return render(request, 'dreambooks/review_edit.html', {'form': form, 'review': review})

@login_required
def review_delete(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if review.author != request.user and not request.user.is_staff:
        return HttpResponseForbidden()
    
    story_slug = review.story.slug
    review.delete()
    return redirect('story_detail', slug=story_slug)

@login_required
def chapter_edit(request, slug, pk):
    story = get_object_or_404(Story, slug=slug)

    # Find FK field to Story
    fk_name = next((f.name for f in Chapter._meta.get_fields() if getattr(f, 'related_model', None) is Story), 'story')
    chapter = get_object_or_404(Chapter, pk=pk, **{fk_name: story})

    # Only author or staff can edit
    if request.user != story.author and not request.user.is_staff:
        return HttpResponseForbidden()

    from .forms import ChapterForm
    if request.method == "POST":
        form = ChapterForm(request.POST, request.FILES, instance=chapter)
        if form.is_valid():
            form.save()
            return redirect('chapter_detail', slug=story.slug, pk=chapter.pk)
    else:
        form = ChapterForm(instance=chapter)

    return render(request, 'dreambooks/chapter_create.html', {
        'form': form,
        'story': story,
        'chapter': chapter,  # can use in template to show "Edit Chapter"
    })

@login_required
def chapter_delete(request, slug, pk):
    story = get_object_or_404(Story, slug=slug)

    fk_name = next((f.name for f in Chapter._meta.get_fields() if getattr(f, 'related_model', None) is Story), 'story')
    chapter = get_object_or_404(Chapter, pk=pk, **{fk_name: story})

    # Only author or staff can delete
    if request.user != story.author and not request.user.is_staff:
        return HttpResponseForbidden()

    if request.method == "POST":
        chapter.delete()
        return redirect('story_detail', slug=story.slug)

    return render(request, 'dreambooks/chapter_delete.html', {
        'story': story,
        'chapter': chapter
    })

def story_list(request):
    q = request.GET.get('q')
    genre_filter = request.GET.get('genre')
    order = request.GET.get('order')  # 'newest', 'oldest', 'rating'

    qs = Story.objects.all().prefetch_related('genres').annotate(avg_rating=Avg('reviews__rating'))

    if q:
        qs = qs.filter(title__icontains=q)

    if genre_filter:
        qs = qs.filter(genres__name=genre_filter)

    if order == 'newest':
        qs = qs.order_by('-created_at')
    elif order == 'oldest':
        qs = qs.order_by('created_at')
    elif order == 'rating':
        qs = qs.order_by('-avg_rating')
    else:
        qs = qs.order_by('-created_at')  # default

    return render(request, 'dreambooks/story_list.html', {
        'stories': qs,
        'query': q,
        'selected_genre': genre_filter,
        'selected_order': order,
        'all_genres': Genre.objects.all(),  # send all genres for the filter dropdown
    })

@login_required
def story_edit(request, slug):
    story = get_object_or_404(Story, slug=slug)

    # Only allow story owner or staff
    if request.user != story.author and not request.user.is_staff:
        raise PermissionDenied

    if request.method == "POST":
        form = StoryForm(request.POST, request.FILES, instance=story)
        if form.is_valid():
            form.save()
            return redirect('story_detail', slug=story.slug)
    else:
        form = StoryForm(instance=story)

    return render(request, 'dreambooks/story_edit.html', {
        'form': form,
        'story': story,
    })

@login_required
def contact_list_create(request):
    if request.method == "POST":
        message_text = request.POST.get("message")
        if message_text:
            ContactMessage.objects.create(user=request.user, message=message_text)
        return redirect("contact")
    
    if request.user.is_staff:
        messages = ContactMessage.objects.all().order_by('-created_at')
    else:
        messages = ContactMessage.objects.filter(user=request.user).order_by('-created_at')

    return render(request, "dreambooks/contact.html", {"messages": messages})


@login_required

@login_required
def contact_edit(request, pk):
    if request.user.is_staff:
        contact = get_object_or_404(ContactMessage, pk=pk)
    else:
        contact = get_object_or_404(ContactMessage, pk=pk, user=request.user)

    if request.method == "POST":
        new_message = request.POST.get("message")
        if new_message:
            contact.message = new_message
            contact.save()
        return redirect("contact")

    return render(request, "dreambooks/contact_edit.html", {"contact": contact})


@login_required
def contact_delete(request, pk):
    if request.user.is_staff:
        contact = get_object_or_404(ContactMessage, pk=pk)
    else:
        contact = get_object_or_404(ContactMessage, pk=pk, user=request.user)

    if request.method == "POST":
        contact.delete()
        return redirect("contact")

    return redirect("contact")

def about(request):
    return render(request, 'dreambooks/about.html')