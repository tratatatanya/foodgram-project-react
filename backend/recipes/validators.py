from django.core.exceptions import ValidationError


def validate_time(value):
    if value < 1:
        raise ValidationError('Еда сама себя не приготовит!')
