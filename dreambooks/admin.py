from .models import Genre, Story, Chapter, ContactMessage
from django.contrib import admin

admin.site.register(Genre)

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'slug')  # show these columns in admin list
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}  # optional: auto-generate slug

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('title', 'story', 'order', 'created_at')
    list_filter = ('story',)
    search_fields = ('title', 'content')

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'message')