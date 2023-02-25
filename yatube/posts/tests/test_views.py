from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.core.cache import cache
from django import forms
from django.urls import reverse
from django.conf import settings

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
        cls.group_test = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-group-2',
            description='Тестовое описание 2',
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

    def show_context(self, post):
        """Функция для передачи контекста."""
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)

    def test_index__group_profil_page_show_correct_context(self):
        """Шаблон index, group, profile сформирован с правильным контекстом."""
        revers = [
            (reverse('posts:index'), None),
            (reverse('posts:group_list', args=(self.group.slug,)), None),
            (reverse('posts:profile', args=(self.user,)), None),
            (reverse('posts:post_detail', args=(self.post.id,)), False),
        ]
        for rever, bool in revers:
            if bool is False:
                response = self.authorized_client.get(rever)
                self.show_context(response.context.get('post'))
            else:
                response = self.authorized_client.get(rever)
                self.show_context(response.context['page_obj'][0])

    def test_create_edit_page_show_correct_form(self):
        """post_create и post-edit сформирован с правильным контекстом."""
        urls = {
            reverse('posts:post_create'),
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}),
        }
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertIsInstance(response.context['form'].fields['text'],
                                      forms.fields.CharField)
                self.assertIsInstance(response.context['form'].fields['group'],
                                      forms.fields.ChoiceField)
                self.assertIsInstance(response.context['form'], PostForm)

    def test_post_appears_at_group(self):
        """Пост НЕ появляется в другой группе."""
        context = {reverse('posts:group_list',
                   kwargs={'slug': self.group.slug}): self.group,
                   reverse('posts:group_list',
                   kwargs={'slug': self.group_test.slug}): self.group_test,
                   }
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group_test.slug}))
        self.assertFalse(response.context['page_obj'])
        for reverse_page, object in context.items():
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_client.get(reverse_page)
                group_object = response.context['group']
                self.assertEqual(group_object.title, object.title)
                self.assertEqual(group_object.slug, object.slug)
                self.assertEqual(group_object.description,
                                 object.description)


class PaginatorViewsTest(TestCase):

    TEST_OF_POST = 13

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create(username='Author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group'
        )
        bilk_post: list = []
        for i in range(self.TEST_OF_POST):
            bilk_post.append(Post(text=f'Тестовый текст {i}',
                                  group=self.group,
                                  author=self.user))
        Post.objects.bulk_create(bilk_post)

    def test_paginator_correct(self):
        """Пагинатор работает корректно."""
        urls = (reverse('posts:index'),
                reverse('posts:profile',
                        kwargs={'username': f'{self.user.username}'}),
                reverse('posts:group_list',
                        kwargs={'slug': f'{self.group.slug}'}))
        for page in urls:
            response_firts_post = self.guest_client.get(page)
            response_secnd_post = self.guest_client.get(page + '?page=2')
            count_posts_first = len(response_firts_post.context['page_obj'])
            count_posts_second = len(response_secnd_post.context['page_obj'])
            self.assertEqual(count_posts_first,
                             settings.PAGES)
            self.assertEqual(count_posts_second,
                             self.TEST_OF_POST - settings.PAGES)
