from ..models import Group, Post, Comment, CUT_TEXT

from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Тестовый комент'
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        title = (
            (self.group, self.group.title),
            (self.post, self.post.text[:CUT_TEXT])
        )
        for fields, expected_name in title:
            with self.subTest(fields=fields):
                self.assertEqual(expected_name, str(fields))

    def test_post_verboses_names(self):
        """Post verbose_name в полях совпадает с ожидаемым."""
        field_verboses = [
            ('text', 'Текст поста'),
            ('pub_date', 'Дата публикации'),
            ('author', 'Автор'),
            ('group', 'Группа'),
            ('image', 'Картинка'),
        ]
        for field, expected_value in field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    PostModelTest.post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_post_help_text(self):
        """Post help_text в полях совпадает с ожидаемым."""
        field_help_texts = [
            ('text', 'Текст нового поста'),
            ('pub_date', 'Укажите дату.'),
            ('author', 'Укажите автора.'),
            ('group', 'Группа, к которой будет относиться пост'),
            ('image', 'Загрузите картинку'),
        ]
        for field, expected_value in field_help_texts:
            with self.subTest(field=field):
                self.assertEqual(
                    PostModelTest.post._meta.get_field(field).help_text,
                    expected_value
                )

    def test_group_verboses_names(self):
        """Group verbose_name в полях совпадает с ожидаемым."""
        field_verboses = [
            ('title', 'Имя'),
            ('slug', 'Адрес'),
            ('description', 'Описание'),
        ]
        for field, expected_value in field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    PostModelTest.group._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_group_help_text(self):
        """Group help_text в полях совпадает с ожидаемым."""
        field_help_texts = [
            ('title', 'Укажите имя группы.'),
            ('slug', 'Укажите адрес группы.'),
            ('description', 'Укажите описание группы.'),
        ]
        for field, expected_value in field_help_texts:
            with self.subTest(field=field):
                self.assertEqual(
                    PostModelTest.group._meta.get_field(field).help_text,
                    expected_value
                )

    def test_comment_verboses_names(self):
        """Comment verbose_name в полях совпадает с ожидаемым."""
        field_verboses = [
            ('post', 'Коментарии'),
            ('text', 'Текст комментария'),
            ('author', 'Автор коментария'),
            ('created', 'Дата комментария'),
        ]
        for field, expected_value in field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    PostModelTest.comment._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_group_help_text(self):
        """Comment help_text в полях совпадает с ожидаемым."""
        field_help_texts = [
            ('text', 'Напишите текст комментария'),
        ]
        for field, expected_value in field_help_texts:
            with self.subTest(field=field):
                self.assertEqual(
                    PostModelTest.comment._meta.get_field(field).help_text,
                    expected_value
                )
