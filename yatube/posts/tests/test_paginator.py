from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PaginatorViewsTest(TestCase):

    TEST_OF_POST = 13

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create(username='Author')
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group'
        )
        bilk_post: list = []
        for number in range(self.TEST_OF_POST):
            bilk_post.append(Post(text=f'Тестовый текст {number}',
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
        for url in urls:
            page_float = self.TEST_OF_POST % settings.PAGES
            page = self.TEST_OF_POST // settings.PAGES
            if page_float > 0:
                response_second_post = self.guest_client.get(
                    f'{url}?page={page+1}'
                )
            else:
                response_second_post = self.guest_client.get(
                    f'{url}?page={page}'
                )
            response_firts_post = self.guest_client.get(url)
            count_posts_first = len(response_firts_post.context['page_obj'])
            count_posts_second = len(response_second_post.context['page_obj'])
            self.assertEqual(count_posts_first,
                             settings.PAGES)
            if page_float > 0:
                self.assertEqual(count_posts_second, page_float)
            else:
                self.assertEqual(count_posts_second, settings.PAGES)
