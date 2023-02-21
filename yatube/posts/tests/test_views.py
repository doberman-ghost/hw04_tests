from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.core.cache import cache
from django import forms
from django.urls import reverse
from django.conf import settings
from django.core.paginator import Paginator

from ..forms import PostForm
from ..models import Post, Group

User = get_user_model()


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.user = User.objects.create_user(username='Author')
        cls.user_no_author = User.objects.create_user(username='NoAuthor')
        cls.post = Post.objects.create(
            text='Пробный текст',
            author=cls.user,
            group=cls.group,
        )
        cls.urls = (
            ('posts:index', None, 'posts/index.html'),
            ('posts:profile', (cls.user,), 'posts/profile.html'),
            ('posts:group_list', (cls.group.slug,), 'posts/group_list.html'),
            ('posts:post_detail', (cls.post.id,), 'posts/post_detail.html'),
            ('posts:post_create', None, 'posts/create_post.html'),
            ('posts:post_edit', (cls.post.id,), 'posts/create_post.html'),
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_no_author = Client()
        self.authorized_client_no_author.force_login(self.user_no_author)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, args, template in self.urls:
            reverse_name = reverse(url, args=args)
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def show_context(self, response, bool=False):
        """Функция для передачи контекста."""
        if bool:
            post = response.context.get('post')
        else:
            post = response.context['page_obj'][0]
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.show_context(response)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', args=(self.group.slug,))
        )
        self.show_context(response)
        self.assertEqual(response.context.get('group'), self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', args=(self.user,))
        )
        self.show_context(response)
        self.assertEqual(response.context.get('author'), self.user)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=(self.post.id,))
        )
        self.show_context(response, True)

    def test_create_edit_page_show_correct_form(self):
        """post_create и post-edit сформирован с правильным контекстом."""
        urls = (
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.id,)),
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ChoiceField,
        }
        for url, slug in urls:
            reverse_name = reverse(url, args=slug)
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get('form').fields.get(
                            value
                        )
                        self.assertIsInstance(form_field, expected)
                        self.assertIsInstance(response.context['form'],
                                              PostForm)

    def test_post_appears_at_group(self):
        """Пост НЕ появляется в другой группе."""
        Post.objects.create(
            author=self.user,
            text='Текстовый текст',
            group=self.group
        )
        group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-group-2',
            description='Тестовое описание 2',
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', args=(group_2.slug,))
        )
        self.assertEqual(len(response.context['page_obj']), 0)


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post_qty = 13
        Post.objects.bulk_create(
            [Post(
                author=cls.user,
                text=f'Тестовая запись{post}',
                group=cls.group
            )for post in range(cls.post_qty)]
        )
        cls.urls = (
            ('posts:index', None),
            ('posts:profile', (cls.user,)),
            ('posts:group_list', (cls.group.slug,)),
        )

    def test_paginator_correct(self):
        """Пагинатор работает корректно."""
        paginator = Paginator(Post.objects.all(), settings.PAGES)
        for url, args in self.urls:
            reverse_name = reverse(url, args=args)
            with self.subTest(reverse_name=reverse_name):
                for page in paginator.page_range:
                    if page < paginator.num_pages:
                        number_page = f'{reverse_name}?page={page}'
                        response = self.client.get(number_page)
                        self.assertEqual(
                            len(response.context['page_obj']),
                            settings.PAGES
                        )
                    end_page = f'{reverse_name}?page={paginator.num_pages}'
                    cache.clear()
                    response = self.client.get(end_page)
                    self.assertEqual(
                        len(response.context['page_obj']),
                        paginator.count - settings.PAGES
                        * (paginator.num_pages - 1)
                    )
