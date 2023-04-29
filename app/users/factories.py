import factory
import factory.random
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory
from logger.factories import generate_club

factory.random.reseed_random(0)  # TODO: Allow configuration of seed
User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.sequence(lambda n: "user%d" % n)
    email = factory.sequence(lambda n: "user%d@caves.app" % n)
    name = factory.Faker("name")
    password = None
    is_active = factory.Faker("pybool", truth_probability=80)
    bio = factory.Faker("text", max_nb_chars=500)
    location = factory.Faker("city")
    clubs = factory.LazyFunction(generate_club)
    page_title = factory.Faker("text", max_nb_chars=40)
    timezone = factory.Faker("timezone")
    public_statistics = factory.Faker("pybool")
    private_notes = factory.Faker("pybool")
    allow_friend_email = factory.Faker("pybool")
    allow_friend_username = factory.Faker("pybool")
    allow_comments = factory.Faker("pybool")
    privacy = factory.Faker(
        "random_element", elements=[User.PUBLIC, User.FRIENDS, User.PRIVATE]
    )
    units = factory.Faker("random_element", elements=[User.METRIC, User.IMPERIAL])

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        kwargs["page_title"] = kwargs["page_title"].replace(".", "")
        return kwargs
