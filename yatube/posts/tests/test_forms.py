import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Author')
        cls.user_no_author = User.objects.create_user(username='NoAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись',
            group=cls.group,
        )
        cls.form = PostForm()
        cls.post_qty = Post.objects.count()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_no_author = Client()
        self.authorized_client_no_author.force_login(self.user_no_author)

    def test_create_form(self):
        """Валидная форма create создает запись в Post."""
        form_data = {
            'text': self.post.text,
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:profile', args=(self.user,)),
            HTTPStatus.FOUND
        )
        self.assertEqual(Post.objects.count(), self.post_qty + 1)
        post = Post.objects.get(pk=2)
        check_post_fields = (
            (post.author, self.post.author),
            (post.text, self.post.text),
            (post.group, self.group),
        )
        for new_post, expected in check_post_fields:
            with self.subTest(new_post=expected):
                self.assertEqual(new_post, expected)

        response = self.authorized_client.get(reverse(
            'posts:group_list', args=(self.group.slug,))
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(
            response.context['page_obj']), Post.objects.count()
        )

    def test_edit_form(self):
        """Валидная форма edit редактирует запись в Post."""
        group_2 = Group.objects.create(
            title='Новая группа',
            slug='new-slug',
            description='Новое описание',
        )
        form_data = {
            'text': 'Новый текст',
            'group': group_2.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=(self.post.id,)),
            HTTPStatus.FOUND
        )
        self.assertEqual(self.post_qty, self.post_qty)
        post = Post.objects.first()
        check_edited_post_fields = (
            (post.author, self.post.author),
            (post.text, post.text),
            (post.group, post.group),
        )
        for new_post, expected in check_edited_post_fields:
            with self.subTest(new_post=expected):
                self.assertEqual(new_post, expected)
        response = self.authorized_client.get(reverse(
            'posts:group_list', args=(self.group.slug,))
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.context['page_obj']), 0)
