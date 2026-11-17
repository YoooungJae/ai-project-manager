# 출처: AI 프로젝트 매니저 최종보고서(2023.12) 부록 4
from django.db import models


class Message(models.Model):
    username = models.CharField(max_length=255)
    room = models.CharField(max_length=255)
    content = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    ai_response1 = models.TextField(null=True, blank=True)
    ai_response2 = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ('date_added',)


class Image(models.Model):
    image = models.ImageField(upload_to='images/')
