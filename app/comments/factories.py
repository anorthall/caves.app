import factory
from comments.models import Comment
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory
from logger.models import Trip

User = get_user_model()


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment

    author = factory.Iterator(User.objects.filter(is_active=True))
    trip = factory.Iterator(Trip.objects.filter(user__allow_comments=True))
    content = factory.Faker("text", max_nb_chars=400)
