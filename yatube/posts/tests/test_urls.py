from http import HTTPStatus

from django.contrib.auth import REDIRECT_FIELD_NAME, get_user_model
from django.test import TestCase, Client
from django.core.cache import cache
from django.urls import reverse
from django.conf import settings

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
        cls.user = User.objects.create(username='Author')
        cls.user_no_author = User.objects.create(username='NoAuthor')
        cls.post = Post.objects.create(
            text='Пробный текст',
            author=cls.user,
            group=cls.group,
        )
        cls.urls = (
            ('posts:index', None, 'posts/index.html', '/',
             HTTPStatus.OK, True),
            ('posts:profile', (cls.user,), 'posts/profile.html',
             f'/profile/{cls.user.username}/', HTTPStatus.OK, True),
            ('posts:group_list', (cls.group.slug,), 'posts/group_list.html',
             f'/group/{cls.group.slug}/', HTTPStatus.OK, True),
            ('posts:post_detail', (cls.post.id,), 'posts/post_detail.html',
             f'/posts/{cls.post.id}/', HTTPStatus.OK, True),
            ('posts:post_create', None, 'posts/create_post.html', '/create/',
             HTTPStatus.OK, False),
            ('posts:post_edit', (cls.post.id,), 'posts/create_post.html',
             f'/posts/{cls.post.id}/edit/', HTTPStatus.OK, False),
            (None, None, None, '/unexisting_page/',
             HTTPStatus.NOT_FOUND, False),
        )

    def setUp(self):
        self.authorized_client_no_author = Client()
        self.authorized_client_no_author.force_login(self.user_no_author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_reverse(self):
        """Проверка реверсов."""
        for url, args, _, link, _, _ in self.urls:
            if url is not None:
                reverse_name = reverse(url, args=args)
                with self.subTest(reverse_name=link):
                    self.assertEqual(reverse_name, link)

    def test_urls_for_user(self):
        """Проверка доступности адресов страниц для всех."""
        for _, _, _, address, status, bol in self.urls:
            with self.subTest(address=address):
                if bol:
                    response = self.client.get(address)
                else:
                    response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_edit_urls_only_for_author(self):
        """Запись может редактировать только автор + перенаправление."""
        users = (
            (self.client,),
            (self.authorized_client_no_author,),
        )
        for user in users:
            with self.subTest(user=user):
                reverse_name = reverse('posts:post_edit', args=(self.post.id,))
                response = self.client.post(reverse_name)
                if user == self.authorized_client_no_author:
                    self.assertRedirects(response, reverse(
                        'posts:post_detail', args=(self.post.id,)),
                    )
                else:
                    login = reverse(settings.LOGIN_URL)
                    self.assertRedirects(
                        response,
                        f'{login}?{REDIRECT_FIELD_NAME}={reverse_name}',
                    )

    def test_urls_redirects_of_an_unauthorized_user(self):
        """Доступности адресов страниц для неавторизованного пользователя."""
        rederict_urls = (
            'posts:post_create',
            'posts:post_edit',

        )
        for url, args, _, _, _, _ in self.urls:
            if url is not None:
                reverse_name = reverse(url, args=args)
                with self.subTest(reverse_name=reverse_name):
                    if url in rederict_urls:
                        response = self.client.get(reverse_name, follow=True)
                        login = reverse(settings.LOGIN_URL)
                        self.assertRedirects(
                            response,
                            f'{login}?{REDIRECT_FIELD_NAME}={reverse_name}',
                        )
                    else:
                        response = self.client.get(reverse_name)
                        self.assertEqual(response.status_code, HTTPStatus.OK)
