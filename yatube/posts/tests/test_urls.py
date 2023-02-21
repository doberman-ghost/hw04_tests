from http import HTTPStatus

from django.contrib.auth import REDIRECT_FIELD_NAME, get_user_model
from django.test import TestCase, Client
from django.core.cache import cache
from django.conf import settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовый текст',
            slug='test-slug'
        )
        cls.user = User.objects.create_user(username='Author')
        cls.user_no_author = User.objects.create_user(username='NoAuthor')
        cls.post = Post.objects.create(
            text='Пробный текст',
            author=cls.user,
            group=cls.group,
        )
        cls.urls = (
            ('posts:index', None, 'posts/index.html', '/'),
            ('posts:profile', (cls.user,), 'posts/profile.html',
             f'/profile/{cls.user.username}/'),
            ('posts:group_list', (cls.group.slug,), 'posts/group_list.html',
             f'/group/{cls.group.slug}/'),
            ('posts:post_detail', (cls.post.id,), 'posts/post_detail.html',
             f'/posts/{cls.post.id}/'),
            ('posts:post_create', None, 'posts/create_post.html', '/create/'),
            ('posts:post_edit', (cls.post.id,), 'posts/create_post.html',
             f'/posts/{cls.post.id}/edit/'),
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_no_author = Client()
        self.authorized_client_no_author.force_login(self.user_no_author)
        cache.clear()

    def test_reverse(self):
        """Проверка реверсов."""
        for url, args, _, link in self.urls:
            reverse_name = reverse(url, args=args)
            with self.subTest(reverse_name=link):
                self.assertEqual(reverse_name, link)

    def test_urls_for_user(self):
        """Проверка доступности адресов страниц для пользователя."""
        redirect_to_post_detail = (
            'posts:post_edit',
        )
        for url, args, _, link in self.urls:
            reverse_name = reverse(url, args=args)
            with self.subTest(reverse_name=link):
                if url in redirect_to_post_detail:
                    response = self.authorized_client_no_author.get(
                        reverse_name, follow=True
                    )
                    redirect = reverse('posts:post_detail', args=args)
                    self.assertRedirects(response, redirect, HTTPStatus.FOUND)
                else:
                    response = self.authorized_client_no_author.get(
                        reverse_name
                    )
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_for_guest(self):
        """Проверка доступности адресов страниц для гостя."""
        rederict_urls = (
            'posts:post_create',
            'posts:post_edit',
        )
        for url, args, _, _ in self.urls:
            reverse_name = reverse(url, args=args)
            with self.subTest(reverse_name=reverse_name):
                if url in rederict_urls:
                    response = self.client.get(reverse_name, follow=True)
                    login = reverse(settings.LOGIN_URL)
                    self.assertRedirects(
                        response,
                        f'{login}?{REDIRECT_FIELD_NAME}={reverse_name}',
                        HTTPStatus.FOUND
                    )
                else:
                    response = self.client.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_404_nonexistent_page(self):
        """Проверка 404 для несуществующих страниц."""
        url = '/unexisting_page/'
        roles = (
            self.authorized_client,
            self.authorized_client_no_author,
            self.client,
        )
        for role in roles:
            with self.subTest(url=url):
                response = role.get(url, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
