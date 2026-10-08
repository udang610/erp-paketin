"""
ERP Paketin - Defensive Security Utilities
Includes IP & Username rate-limiting using Django standard cache backend.
"""
from django.core.cache import cache
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip


def check_rate_limit(request, action='login', max_attempts=10, timeout_seconds=300):
    """
    Checks and increments failed attempt counter per IP address.
    Returns True if rate limit is exceeded, False otherwise.
    """
    ip = get_client_ip(request)
    cache_key = f"ratelimit:{action}:{ip}"
    attempts = cache.get(cache_key, 0)
    
    if attempts >= max_attempts:
        return True
    return False


def record_failed_attempt(request, action='login', timeout_seconds=300):
    ip = get_client_ip(request)
    cache_key = f"ratelimit:{action}:{ip}"
    attempts = cache.get(cache_key, 0) + 1
    cache.set(cache_key, attempts, timeout=timeout_seconds)
    return attempts


def clear_rate_limit(request, action='login'):
    ip = get_client_ip(request)
    cache_key = f"ratelimit:{action}:{ip}"
    cache.delete(cache_key)


class CustomLoginView(LoginView):
    """
    Custom LoginView with built-in rate-limiting protection against brute-force attacks.
    """
    template_name = 'registration/login.html'
    redirect_authenticated_user = False

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/')
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if check_rate_limit(request, action='login', max_attempts=10, timeout_seconds=300):
            messages.error(
                request,
                'Terlalu banyak percobaan login gagal dari perangkat ini. Demi keamanan, harap tunggu 5 menit sebelum mencoba kembali.'
            )
            return self.render_to_response(self.get_context_data(form=self.get_form()))

        response = super().post(request, *args, **kwargs)
        
        # If login was successful, clear rate limit
        if request.user.is_authenticated:
            clear_rate_limit(request, action='login')
        else:
            # If form was invalid / login failed, increment failure counter
            record_failed_attempt(request, action='login', timeout_seconds=300)

        return response


class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        from django.contrib.auth import logout
        logout(request)
        return redirect('accounts:login')
