from decouple import config

ENV = config("DJANGO_ENV", default="dev")  # dev, prod
if ENV == "prod":
    from .prod import *
else:
    from .dev import *
