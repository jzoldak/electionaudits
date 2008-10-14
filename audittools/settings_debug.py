from settings import *
DEBUG = True
TEMPLATE_DEBUG = DEBUG
INTERNAL_IPS = ["127.0.0.1"]

INSTALLED_APPS += (
    'lukeplant_me_uk.django.validator',
    'django_extensions',
    'debug_toolbar',
)

MIDDLEWARE_CLASSES = (
    'lukeplant_me_uk.django.validator.middleware.ValidatorMiddleware',
) + MIDDLEWARE_CLASSES

MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
