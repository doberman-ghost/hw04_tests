from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


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
        related_name='posts',
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="Группа",
        help_text="Группа, к которой будет относиться пост",
        related_name='posts',
    )

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:settings.CUT_TEXT]
