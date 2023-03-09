from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .utils import paginator
from .forms import PostForm, CommentForm
from .models import Post, Group, Follow, User


@cache_page(60 * 20, key_prefix='index_page')
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
    following = None
    if request.user.is_authenticated:
        following = author.following.filter(user=request.user).exists()
    context = {
        'page_obj': paginator(post_list, request),
        'author': author,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Страница одной записи."""
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        pk=post_id)
    comments = post.comments.select_related('author')
    context = {
        'post': post,
        'form': CommentForm(),
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Функция создания записи."""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
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
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    """Функция создания комментариев."""
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Функция страницы с подписками."""
    posts = Post.objects.select_related('author', 'group').prefetch_related(
        'comments').filter(
        author__following__user=request.user
    )
    context = {
        'page_obj': paginator(posts, request),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Функция подписки на автора."""
    author = get_object_or_404(User, username=username)
    follower = request.user
    if author != follower and follower != author.follower:
        Follow.objects.get_or_create(user=follower, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        user=request.user,
        author__username=username,
    ).delete()
    return redirect('posts:profile', username)
