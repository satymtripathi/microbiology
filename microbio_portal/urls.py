# microbio_portal/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

# Ensure imports are minimal and correct for the project level
# Only import standard Django components needed for project configuration

urlpatterns = [
    path('admin/', admin.site.urls),
    # 1. DELEGATE ALL APPLICATION LOGIC TO CORE.URLS
    path('', include('core.urls')),
    # Explicitly ensure /accounts/logout/ uses our logout_view to avoid 405s
    path('accounts/logout/', core_views.logout_view, name='accounts_logout'),
    # Built-in Auth URLs (kept under /accounts/ for defaults) - placed after core to avoid name collisions
    path('accounts/', include('django.contrib.auth.urls')),
]

# IMPORTANT: This block is necessary to serve media files (images) during development!
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)