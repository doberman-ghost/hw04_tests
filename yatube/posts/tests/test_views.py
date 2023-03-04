from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.core.cache import cache
from django.urls import reverse

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
            if bool:
                response = self.authorized_client.get(rever)
                self.show_context(response.context['page_obj'][0])
            else:
                response = self.authorized_client.get(rever)
                self.show_context(response.context.get('post'))

    def test_create_edit_page_show_correct_form(self):
        """post_create и post-edit сформирован с правильным контекстом."""
        urls = (
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.id,)),
        )
        for url, slug in urls:
            reverse_name = reverse(url, args=slug)
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIsInstance(response.context['form'], PostForm)

    def test_post_appears_at_group(self):
        """Пост НЕ появляется в другой группе."""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group_test.slug}))
        self.assertNotEqual(response.context['group'], self.post.group)

    def test_objects_group_author(self):
        """Проверка передачи объектов 'group' и 'author'"""
        urls = [
            (reverse('posts:group_list', args=(self.group.slug,)),
             'group', self.group),
            (reverse('posts:profile', args=(self.user,)), 'author', self.user)
        ]
        for url, name, field in urls:
            response = self.authorized_client.get(url)
            form_field = response.context.get(name)
            with self.subTest(form_field=form_field):
                self.assertEqual(form_field, field)
