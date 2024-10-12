from django.contrib import admin
from .models import CourseEventModel, CourseEventTime, DeadlineEventModel, UserStudySetting

# Register your models here.
admin.site.register(CourseEventModel)
admin.site.register(CourseEventTime)
admin.site.register(DeadlineEventModel)
admin.site.register(UserStudySetting)
