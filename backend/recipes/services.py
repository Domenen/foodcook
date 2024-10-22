from django.utils.crypto import get_random_string


def generate_url_slug(model_class, length):
    while True:
        url_slug = get_random_string(length=length)
        if not model_class.objects.filter(url_slug=url_slug).exists():
            return url_slug
