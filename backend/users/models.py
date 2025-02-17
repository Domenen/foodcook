from django.contrib.auth.models import AbstractUser, UnicodeUsernameValidator
from django.db import models
from django.db.models import EmailField
from django.forms import ValidationError

from api.constants import MAX_LENGTH_NAME, MAX_LENGTH_EMAIL


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=MAX_LENGTH_NAME,
        unique=True,
        help_text='ведите имя пользователя '
                  '(Только буквы, цифры и символы:  @/./+/-/_ )',
        validators=(UnicodeUsernameValidator(),),
        error_messages={
            'unique': 'Пользователь с таким логином уже существует.',
        },
    )
    first_name = models.CharField(
        verbose_name='Имя',
        help_text='Введите имя',
        max_length=MAX_LENGTH_NAME,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        help_text='Введите фамилию',
        max_length=MAX_LENGTH_NAME,
    )
    email = EmailField(
        verbose_name='E-mail',
        help_text='Введите адрес электронной почты',
        max_length=MAX_LENGTH_EMAIL,
        unique=True,
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to='media/users/',
        blank=True,
        null=True
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.get_full_name()


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions_user',
        verbose_name='Пользователь',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions_on_author',
        verbose_name='Автор',
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_user_author'
            ),
        )
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'

    def clean(self):
        if self.user == self.author:
            raise ValidationError(
                'Нельзя подписать пользователя на самого себя!'
            )
