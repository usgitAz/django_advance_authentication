from uuid import uuid4

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from apps.accounts.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    id = factory.LazyFunction(uuid4)
    email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_staff = False
    is_active = True
    date_joined = factory.LazyFunction(timezone.now)

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if create:
            password = extracted or "password1234"
            self.set_password(password)
            self.save()
