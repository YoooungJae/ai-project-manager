# 출처: AI 프로젝트 매니저 최종보고서(2023.12) 부록 4
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("<str:room_name>/", views.room, name="room"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
