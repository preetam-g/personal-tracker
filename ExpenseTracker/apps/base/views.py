from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

def delete_object_view(request, model, obj_id, final_redirect: str , name: str = None):

    obj = get_object_or_404(model, id=obj_id, user=request.user)
    if not name: name = getattr(obj, 'name', str(obj))

    if request.method == 'POST':
        cnt, _ = obj.delete()

        if cnt:
            messages.success(request, f'{name} successfully deleted.')
        else:
            messages.error(request, 'Failed to delete. Try again later.')

    return redirect(final_redirect)