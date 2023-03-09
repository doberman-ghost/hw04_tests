from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

CUT_TEXT = 15


class Group(models.Model):
    title = models.CharField(
        verbose_name="Имя",
        help_text="Укажите имя группы.",
        max_length=200,
    )
    slug = models.SlugField(
        verbose_name="Адрес",
        help_text="Укажите адрес группы.",
        unique=True,
    )
    description = models.TextField(
        verbose_name="Описание",
        help_text="Укажите описание группы.",
    )

    def __str__(self) -> str:
        return self.title

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"


class Post(models.Model):
    text = models.TextField(
        verbose_name="Текст поста",
        help_text="Текст нового поста",
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации",
        help_text="Укажите дату.",
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        help_text="Укажите автора.",
        related_name="posts",
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="Группа",
        help_text="Группа, к которой будет относиться пост",
        related_name="posts",
    )
    image = models.ImageField(
        verbose_name="Картинка",
        upload_to="posts/",
        blank=True,
        help_text="Загрузите картинку",
    )

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "Пост"
        verbose_name_plural = "Посты"

    def __str__(self):
        return self.text[:CUT_TEXT]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name="Коментарии",
        related_name="comments",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор коментария",
        related_name="comments",
    )
    text = models.TextField(
        verbose_name="Текст комментария",
        help_text="Напишите текст комментария",
    )
    created = models.DateTimeField(
        verbose_name="Дата комментария",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self):
        return self.text[:CUT_TEXT]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Подписчик",
        related_name="follower",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name="following",
    )

    class Meta:
        verbose_name = "Подписчик"
        verbose_name_plural = "Подписчики"
