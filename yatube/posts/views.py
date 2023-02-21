from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from .utils import paginator
from .forms import PostForm
from .models import Post, Group, User


def index(request):
    """Главная страница с записями."""
    post_list = Post.objects.select_related('author', 'group')
    context = {
        'page_obj': paginator(post_list, request),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Страница сообществ с записями."""
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')
    context = {
        'group': group,
        'page_obj': paginator(post_list, request),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Страница автора с его записями."""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group')
    context = {
        'page_obj': paginator(post_list, request),
        'author': author,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Страница одной записи."""
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        pk=post_id)
    context = {
        'post': post,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Функция создания записи."""
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author.username)
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    """Функция редактирования записи."""
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)
