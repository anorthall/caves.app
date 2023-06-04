import zoneinfo
from datetime import datetime, timedelta

import factory
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from factory import random
from factory.django import DjangoModelFactory
from faker import Faker

from .models import Trip, TripReport

fake = Faker()

# Configuration for maximum length of longer trips
MAX_LONG_TRIP_LENGTH_IN_DAYS = 10
MAX_LONG_TRIP_LENGTH_IN_HOURS = MAX_LONG_TRIP_LENGTH_IN_DAYS * 24
MAX_LONG_TRIP_LENGTH_IN_MINUTES = MAX_LONG_TRIP_LENGTH_IN_HOURS * 60

# Configuration for maximum length of shorter trips
MAX_SHORT_TRIP_LENGTH_IN_HOURS = 14
MAX_SHORT_TRIP_LENGTH_IN_MINUTES = MAX_SHORT_TRIP_LENGTH_IN_HOURS * 60


def _get_caver_list():
    names_list = []
    for _ in range(random.randgen.randint(0, 5)):
        names_list.append(fake.name())
    return ", ".join(names_list)


def _generate_distance(min, max, chance_of_none=0.2):
    if (chance_of_none * 100) > random.randgen.randint(1, 100):
        return None

    num = random.randgen.randint(min, max)
    return f"{num}m"


def _generate_aid_dist():
    return _generate_distance(20, 80, 0.95)


def _generate_vert_dist_up():
    return _generate_distance(10, 200, 0.3)


def _generate_horizontal_dist():
    return _generate_distance(10, 200, 0.6)


def _generate_surveyed_dist():
    return _generate_distance(10, 800, 0.8)


def _generate_resurveyed_dist():
    return _generate_distance(10, 800, 0.9)


def _generate_expedition():
    if random.randgen.randint(1, 100) > 20:
        return ""

    suffixes = [
        "Cave Project",
        "Cave Expedition",
        "Cave Exploration",
        "Cave Survey",
        "Cave Dig",
        "Diggers",
        "Explorers",
        "Surveyors",
        "Cave Diving",
        "Potholers",
        "Cavers",
        "Project",
    ]

    return fake.city() + " " + random.randgen.choice(suffixes)


def _generate_cave_entrance_or_exit():
    if random.randgen.randint(1, 100) > 20:
        return ""
    return _generate_cave_name()


def _generate_cave_name():
    suffixes = [
        "Cave",
        "Pot",
        "Mine",
        "Shaft",
        "Adit",
        "Tunnel",
        "Rift",
        "Swallet",
        "Sink",
        "Rise",
        "Spring",
        "Sump",
        "Chamber",
        "Passage",
        "Aven",
        "Pitch",
        "Cavern",
        "Grotto",
        "Grot",
        "Caverns",
        "Caves",
        "Pots",
        "Pothole",
        "Potholes",
        "Mines",
        "Shafts",
        "Adits",
        "Tunnels",
        "Chambers",
    ]

    return fake.city() + " " + random.randgen.choice(suffixes)


def generate_club():
    if random.randgen.randint(1, 100) > 60:
        return ""

    middle_choices = [
        "Caving",
        "Potholing",
        "Spelunking",
        "Cave Diving",
        "Cave Exploration",
        "Cave Survey",
        "Digging",
        "Mining",
        "Diggers",
        "Cavers",
        "Explorers",
        "Surveyors",
        "Potholers",
        "Speleologists",
        "Speleology",
        "Cave Research",
        "Cave Science",
        "Cave Rescue",
    ]

    suffixes = [
        "Club",
        "Society",
        "Group",
        "Team",
        "Association",
        "Federation",
        "Union",
        "Trust",
        "Foundation",
        "Institute",
        "Institution",
        "Society",
    ]

    city = fake.city()
    middle = random.randgen.choice(middle_choices)
    suffix = random.randgen.choice(suffixes)
    return f"{city} {middle} {suffix}"


class TripFactory(DjangoModelFactory):
    class Meta:
        model = Trip

    user = factory.Iterator(get_user_model().objects.filter(is_active=True))
    cave_name = factory.LazyFunction(_generate_cave_name)
    cave_entrance = factory.LazyFunction(_generate_cave_entrance_or_exit)
    cave_exit = factory.LazyFunction(_generate_cave_entrance_or_exit)
    cave_region = factory.Faker("city")
    cave_country = factory.Faker("country")
    cave_url = factory.Faker("url")
    type = factory.Faker(
        "random_element",
        elements=[
            Trip.SPORT,
            Trip.DIGGING,
            Trip.SURVEY,
            Trip.EXPLORATION,
            Trip.AID,
            Trip.PHOTO,
            Trip.TRAINING,
            Trip.RESCUE,
            Trip.SCIENCE,
            Trip.HAULING,
            Trip.RIGGING,
            Trip.SURFACE,
            Trip.OTHER,
        ],
    )
    aid_dist = factory.LazyFunction(_generate_aid_dist)
    vert_dist_up = factory.LazyFunction(_generate_vert_dist_up)
    horizontal_dist = factory.LazyFunction(_generate_horizontal_dist)
    surveyed_dist = factory.LazyFunction(_generate_surveyed_dist)
    resurveyed_dist = factory.LazyFunction(_generate_resurveyed_dist)
    start = factory.Faker(
        "date_time_between",
        tzinfo=zoneinfo.ZoneInfo("UTC"),
        start_date=datetime.now() - timedelta(days=365 * 5),
    )
    clubs = factory.LazyFunction(generate_club)
    cavers = factory.LazyFunction(_get_caver_list)
    expedition = factory.LazyFunction(_generate_expedition)
    privacy = factory.Faker(
        "random_element",
        elements=[Trip.PUBLIC, Trip.FRIENDS, Trip.PRIVATE, Trip.DEFAULT],
    )
    notes = factory.Faker("text", max_nb_chars=400)

    @factory.lazy_attribute
    def end(self):
        """Produce the end datetime

        There is an 80% chance of a Trip having an 'end' datetime.
        If it does have one, there is a 1% chance that it will be
        a longer trip (i.e. more than 1 day).
        """
        if random.randgen.randint(1, 100) > 80:
            return None

        if random.randgen.randint(1, 100) > 99:
            return self.start + timedelta(
                minutes=random.randgen.randint(60, MAX_LONG_TRIP_LENGTH_IN_MINUTES)
            )

        return self.start + timedelta(
            minutes=random.randgen.randint(1, MAX_SHORT_TRIP_LENGTH_IN_MINUTES)
        )

    @factory.lazy_attribute
    def vert_dist_down(self):
        """Produce the vertical distance down

        This will only be generated if the Trip has a vertical distance up
        """
        # If there is no vertical distance up, there will be no vertical distance down
        if self.vert_dist_up is None:
            return None

        # There is a 5% chance of there being no vertical distance down
        if random.randgen.randint(1, 100) > 95:
            return None

        # There is a 20% chance of the vertical distance down
        # being different to the vertical distance up
        if random.randgen.randint(1, 100) > 80:
            vert_dist = int(self.vert_dist_up[:-1])
            min = vert_dist - 100 if vert_dist > 100 else 0
            max = vert_dist + 100
            return f"{random.randgen.randint(min, max)}m"

        return self.vert_dist_up

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        kwargs["cave_name"] = kwargs["cave_name"].replace(".", "")
        return kwargs


class TripReportFactory(DjangoModelFactory):
    class Meta:
        model = TripReport

    title = factory.Faker("sentence", nb_words=5)
    slug = factory.LazyAttribute(lambda o: slugify(o.title))
    content = factory.Faker("text", max_nb_chars=4000)
    trip = factory.Iterator(Trip.objects.filter(report=None))

    @factory.lazy_attribute
    def pub_date(self):
        return (self.trip.start + timedelta(days=random.randgen.randint(1, 60))).date()

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        kwargs["title"] = kwargs["title"].replace(".", "")

        user = kwargs.get("user", None)
        if user is None:
            kwargs["user"] = kwargs["trip"].user

        return kwargs


# TODO: Refactor comments
# class CommentFactory(DjangoModelFactory):
#     class Meta:
#         model = Comment

#     author = factory.Iterator(get_user_model().objects.filter(is_active=True))
#     content_object = factory.Iterator(Trip.objects.filter(user__allow_comments=True))
#     content = factory.Faker("text", max_nb_chars=400)
