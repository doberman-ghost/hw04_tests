import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_check = Group.objects.create(
            title='Новая группа',
            slug='new-slug',
            description='Новое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись',
            group=cls.group,
        )
        cls.POST_QTY = 1

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_form(self):
        """Валидная форма create создает запись в Post."""
        form_data = {
            'text': 'Тестовая запись 2',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post = Post.objects.get(pk=2)
        check_edited_post_fields = (
            (post.author, self.post.author),
            (post.text, 'Тестовая запись 2'),
            (post.group.id, self.post.group.id),
        )
        for new_post, expected in check_edited_post_fields:
            with self.subTest(new_post=expected):
                self.assertEqual(new_post, expected)
        self.assertTrue(Post.objects.filter(
                        text=self.post.text,
                        group=self.group,
                        author=self.user
                        ).exists(), 'Поcт не добавлен в базу данных'
                        )

    def test_edit_form(self):
        """Валидная форма edit редактирует запись в Post."""
        form_data = {
            'text': 'Новый текст',
            'group': self.group_check.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(Post.objects.filter(
                        group=self.group_check,
                        author=self.user,
                        pub_date=self.post.pub_date
                        ).exists()
                        )
        post = Post.objects.get(pk=1)
        check_edited_post_fields = (
            (post.author, self.post.author),
            (post.text, 'Новый текст'),
            (post.group.id, self.group_check.id),
        )
        for new_post, expected in check_edited_post_fields:
            with self.subTest(new_post=expected):
                self.assertEqual(new_post, expected)
