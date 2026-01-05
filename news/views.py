from django.shortcuts import render, get_object_or_404
from .models import NewsPost

def news_list(request):
    qs = NewsPost.objects.filter(is_published=True)
    featured_posts = qs.filter(highlight=True)[:5]
    other_posts = qs.exclude(id__in=[p.id for p in featured_posts])[:20]
    return render(
        request,
        "news/news_list.html",
        {"featured_posts": featured_posts, "other_posts": other_posts},
    )

def news_detail(request, slug):
    post = get_object_or_404(NewsPost, slug=slug, is_published=True)
    return render(request, "news/news_detail.html", {"post": post})
