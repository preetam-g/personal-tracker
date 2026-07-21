from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme


def get_safe_next_url(request, fallback=None):
    """
    Return the safe 'next' URL from POST or GET.
    Return the fallback if 'next' is missing or unsafe.
    """
    next_url = request.GET.get('next')

    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
    ):
        return next_url

    return fallback


def redirect_to_next(request, fallback):
    return redirect(get_safe_next_url(request, fallback))