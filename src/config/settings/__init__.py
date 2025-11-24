"""
Select which settings to load.
- dev  : development
- test : pytest / testing
- prod : production
"""

import sys

from decouple import config

from .base import *

# If running pytest, always load test settings
if "pytest" in sys.modules:
    from .test import *
    from config.logging.testing import LOGGING
else:
    ENV = config("DJANGO_ENV", default="dev").lower()
    if ENV not in ["dev", "test", "prod"]:
        print("DJANGO_ENV must be one of: dev, test, prod")
        sys.exit(1)

    if ENV == "prod":
        from config.logging.production import LOGGING
        from .prod import *

    elif ENV == "test":
        from config.logging.testing import LOGGING
        from .test import *
    else:
        from config.logging.development import LOGGING
        from .dev import *
