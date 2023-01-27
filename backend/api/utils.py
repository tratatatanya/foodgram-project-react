from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from recipes.models import Recipe


def custom_post(request, id, serializer):
    user_id = request.user.id
    data = {'user': user_id, 'recipe': id}
    serializer = serializer(data=data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)

def custom_delete(request, id, model):
    user = request.user
    recipe = get_object_or_404(Recipe, id=id)
    deleting_obj = model.objects.filter(user=user, recipe=recipe)
    if not deleting_obj:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    deleting_obj.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)