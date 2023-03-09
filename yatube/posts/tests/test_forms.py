from http import HTTPStatus
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, Comment

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
        cls.bytes_image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
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
        Post.objects.all().delete()
        post_count = Post.objects.count()
        image = SimpleUploadedFile(
            name='new_small.gif',
            content=self.bytes_image,
            content_type='image/gif'
        )
        form_data = {
            'text': self.post.text,
            'group': self.group.id,
            'image': image,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count + self.POST_QTY)
        post = Post.objects.latest('group')
        check_edited_post_fields = (
            (post.author, self.user),
            (post.text, form_data['text']),
            (post.group.id, form_data['group']),
            (post.image, f'posts/{image}'),
        )
        for new_post, expected in check_edited_post_fields:
            with self.subTest(new_post=expected):
                self.assertEqual(new_post, expected)

    def test_edit_form(self):
        """Валидная форма edit редактирует запись в Post."""
        image = SimpleUploadedFile(
            name='new_small.gif',
            content=self.bytes_image,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый текст',
            'group': self.group_check.id,
            'image': image,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post = Post.objects.get(pk=self.post.id)
        check_edited_post_fields = (
            (post.author, self.post.author),
            (post.text, form_data['text']),
            (post.group.id, form_data['group']),
            (post.image, post.image)
        )
        for new_post, expected in check_edited_post_fields:
            with self.subTest(new_post=expected):
                self.assertEqual(new_post, expected)

    def test_comment_for_registered_users(self):
        """Комментарии могут оставлять зарегистрированные пользователи.
        + комментарий появляется на странице"""
        comment_count = Comment.objects.count()
        comment_data = {
            'text': 'тестовый коммент',
        }
        reverse_name = reverse('posts:add_comment', args=(self.post.id,))
        response = self.authorized_client.post(reverse_name,
                                               data=comment_data,
                                               follow=True,
                                               )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=(self.post.id,))
        )
        comment = Comment.objects.first()
        self.assertEqual(comment.text, comment_data['text'])
        self.assertEqual(Comment.objects.count(),
                         comment_count + self.POST_QTY)
