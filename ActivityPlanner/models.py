from django.contrib.auth.models import User
from django.db import models


class CourseEventTime(models.Model):
    weekday = models.CharField(max_length=10)
    start = models.IntegerField()
    end = models.IntegerField()


class UserStudySetting(models.Model):
    semester_start = models.DateField()
    semester_end = models.DateField()
    preferred_study_start = models.IntegerField()
    preferred_study_end = models.IntegerField()
    study_level = models.CharField(max_length=10)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class CourseEventModel(models.Model):
    course_name = models.CharField(max_length=8)
    session = models.CharField(max_length=7)
    event_type = models.CharField(max_length=10)
    time = models.ForeignKey(CourseEventTime, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class DeadlineEventModel(models.Model):
    course_name = models.CharField(max_length=8)
    session = models.CharField(max_length=7)
    event_type = models.CharField(max_length=10)
    deadline_date = models.DateField()
    deadline_time = models.IntegerField(default=86340000)

