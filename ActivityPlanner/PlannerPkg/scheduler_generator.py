# Main Scheduler Class
import uuid
import warnings
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from datetime import timedelta, time

import icalendar

from .data_types import StudyTask


class BaseStudyScheduleGenerator(ABC):
    def __init__(self, courses, study_level, preferred_study_start, preferred_study_end, semester_start_date,
                 semester_end_date):
        self.courses = courses
        self.study_level = study_level
        self.preferred_study_start = preferred_study_start
        self.preferred_study_end = preferred_study_end
        self.semester_start_date = semester_start_date
        self.semester_end_date = semester_end_date
        self.schedule = None

    @abstractmethod
    def generate_schedule(self):
        pass

    @abstractmethod
    def get_schedule(self):
        return self.schedule

    def get_ical(self) -> icalendar.Calendar:
        pass

    @abstractmethod
    def get_raw_ical(self) -> bytes:
        pass


class BetaStudyScheduleGenerator(BaseStudyScheduleGenerator):
    STUDY_LEVEL = {'Basic': 3, 'Normal': 4, 'Advanced': 6}

    # Priority constants
    LOWEST = 20
    MEDIUM_LOW = 40
    MEDIUM = 50
    MEDIUM_HIGH = 70
    HIGH = 80
    HIGHEST = 100

    # Task durations
    PREVIEW_LECTURE_FOR = 1
    REVIEW_LECTURE_FOR = 0.5
    PREVIEW_TUTORIAL_FOR = 1
    PREPARE_LAB_FOR = 1
    STUDY_ASSESSMENT_FOR = 1.5


    def __init__(self, courses, study_level, preferred_study_start, preferred_study_end, semester_start_date,
                 semester_end_date):
        super().__init__(
            courses,
            study_level,
            preferred_study_start,
            preferred_study_end,
            semester_start_date,
            semester_end_date
        )

        self.schedule = defaultdict(lambda: {'tasks': [], 'scheduled_course_time': 0, 'scheduled_study_time': 0})
        self.max_study_time_per_day = self.get_max_study_time_per_day()
        self.study_days_per_week = list(range(7))
        self.tasks = []

    def generate_schedule(self):
        self.load_fixed_course_events()
        self.adjust_daily_max_study_time()
        self.generate_additional_study_tasks()
        self.assign_priorities()
        self.schedule_non_fixed_date_tasks()
        self.adjust_schedule_for_overloads()
        self.finalize_schedule()
        self.generate_ical_file('study_schedule.ics')

    def get_max_study_time_per_day(self):
        if self.study_level in self.STUDY_LEVEL:
            return self.STUDY_LEVEL[self.study_level]
        else:
            return 4  # Default to Normal

    def load_fixed_course_events(self):
        for course in self.courses:
            for course_events in [course.lectures, course.tutorials, course.labs]:
                for event in course_events:
                    task = StudyTask(
                        description=f'{course.course_name} {event.description}',
                        course_name=course.course_name,
                        duration=(datetime.combine(event.date, event.end_time) -
                                  datetime.combine(event.date, event.start_time)).total_seconds() / 3600,
                        earliest_start_date=event.date,
                        latest_end_date=event.date,
                        fixed_date=True,
                        start_time=event.start_time,
                        end_time=event.end_time,
                        priority=BetaStudyScheduleGenerator.HIGHEST  # Highest priority
                    )
                    self.schedule[event.date]['tasks'].append(task)
                    self.schedule[event.date]['scheduled_course_time'] += task.duration

    def adjust_daily_max_study_time(self):
        for date, info in self.schedule.items():
            available_study_time = self.max_study_time_per_day - info['scheduled_course_time']
            if available_study_time < 0:
                available_study_time = 0
            info['available_study_time'] = available_study_time

    def generate_additional_study_tasks(self):
        for course in self.courses:
            # Lecture-related tasks
            for lecture in course.lectures:
                # Lecture Preview (1 day before)
                preview_date = lecture.date - timedelta(days=1)
                if preview_date >= self.semester_start_date:
                    task = StudyTask(
                        description=f"Preview Lecture: {lecture.course_name} {lecture.description}",
                        course_name=course.course_name,
                        duration=BetaStudyScheduleGenerator.PREVIEW_LECTURE_FOR,
                        earliest_start_date=preview_date,
                        latest_end_date=preview_date,
                        fixed_date=False,
                        priority=BetaStudyScheduleGenerator.MEDIUM,
                        splittable=False
                    )
                    self.tasks.append(task)

                # Lecture Reviews
                review_intervals = [0, 3, 7]  # Days after lecture
                for days_after in review_intervals:
                    review_date = lecture.date + timedelta(days=days_after)
                    if review_date <= self.semester_end_date:
                        task = StudyTask(
                            description=f"Review Lecture: {lecture.course_name} {lecture.description}",
                            course_name=course.course_name,
                            duration=BetaStudyScheduleGenerator.REVIEW_LECTURE_FOR,
                            earliest_start_date=review_date,
                            latest_end_date=review_date,
                            fixed_date=False,
                            priority=BetaStudyScheduleGenerator.LOWEST,
                            splittable=False
                        )
                        self.tasks.append(task)

            # Tutorial-related tasks
            for tutorial in course.tutorials:
                # Tutorial Preview (1 day before)
                preview_date = tutorial.date - timedelta(days=1)
                if preview_date >= self.semester_start_date:
                    task = StudyTask(
                        description=f"Preview Tutorial: {tutorial.course_name} {tutorial.description}",
                        course_name=course.course_name,
                        duration=BetaStudyScheduleGenerator.PREVIEW_TUTORIAL_FOR,
                        earliest_start_date=preview_date,
                        latest_end_date=preview_date,
                        fixed_date=False,
                        priority=BetaStudyScheduleGenerator.MEDIUM_LOW,
                        splittable=False
                    )
                    self.tasks.append(task)

            # Lab-related tasks
            for lab in course.labs:
                # Lab Preparation (1 day before)
                preview_date = lab.date - timedelta(days=1)
                if preview_date >= self.semester_start_date:
                    task = StudyTask(
                        description=f"Prepare for Lab: {lab.course_name} {lab.description}",
                        course_name=course.course_name,
                        duration=BetaStudyScheduleGenerator.PREPARE_LAB_FOR,
                        earliest_start_date=preview_date,
                        latest_end_date=preview_date,
                        fixed_date=False,
                        priority=BetaStudyScheduleGenerator.MEDIUM_LOW,
                        splittable=False
                    )
                    self.tasks.append(task)

            # Assignments
            for assignment in course.assignments:
                estimated_duration = assignment.estimated_duration
                suggested_start_date = assignment.suggested_start_time
                latest_end_date = assignment.deadline - timedelta(days=1)
                task = StudyTask(
                    description=f"Work on {assignment.course_name}'s {assignment.assignment_name}",
                    course_name=course.course_name,
                    duration=0,  # Will be determined during scheduling
                    earliest_start_date=suggested_start_date,
                    latest_end_date=latest_end_date,
                    fixed_date=False,
                    priority=BetaStudyScheduleGenerator.MEDIUM_HIGH,
                    splittable=True,
                    total_duration=estimated_duration
                )
                self.tasks.append(task)

            # Assessments Study Sessions
            for assessment in course.assessments:
                study_start_date = assessment.deadline - timedelta(days=14)  # Start 14 days before assessment
                for i in range(14):
                    study_date = study_start_date + timedelta(days=i)
                    if self.semester_start_date <= study_date <= self.semester_end_date:
                        task = StudyTask(
                            description=f"Study for {assessment.course_name} {assessment.assessment_name}",
                            course_name=course.course_name,
                            duration=BetaStudyScheduleGenerator.STUDY_ASSESSMENT_FOR,
                            earliest_start_date=study_date,
                            latest_end_date=study_date,
                            fixed_date=False,
                            priority=BetaStudyScheduleGenerator.HIGH,
                            splittable=False
                        )
                        self.tasks.append(task)

    def assign_priorities(self):
        # Adjust priorities based on deadlines and durations
        for task in self.tasks:
            # Increase priority for tasks with imminent deadlines
            days_until_deadline = (task.latest_end_date - datetime.today()).days
            if days_until_deadline <= 3:
                task.priority += 20
            elif days_until_deadline <= 7:
                task.priority += 10

            # Increase priority for tasks with longer durations
            if task.total_duration and task.total_duration >= 8:
                task.priority += 10

    def schedule_non_fixed_date_tasks(self):
        # Sort tasks by priority (higher first)
        self.tasks.sort(key=lambda x: x.priority, reverse=True)

        for task in self.tasks:
            remaining_duration = task.total_duration if task.total_duration else task.duration
            date = task.earliest_start_date

            while remaining_duration > 0 and date <= task.latest_end_date:
                # Check if date is within study days
                if date.weekday() not in self.study_days_per_week:
                    date += timedelta(days=1)
                    continue

                info = self.schedule[date]
                available_study_time = info.get('available_study_time', self.max_study_time_per_day -
                                                info['scheduled_course_time'] - info['scheduled_study_time'])

                # Adjust available study time if negative
                if available_study_time <= 0:
                    date += timedelta(days=1)
                    continue

                # Determine allocatable time
                allocatable_time = min(available_study_time, remaining_duration, 2)  # Max 2-hour sessions
                if allocatable_time <= 0:
                    date += timedelta(days=1)
                    continue

                # Schedule task portion
                scheduled_task = StudyTask(
                    description=task.description,
                    course_name=task.course_name,
                    duration=allocatable_time,
                    earliest_start_date=date,
                    latest_end_date=date,
                    fixed_date=False,
                    priority=task.priority,
                    splittable=task.splittable
                )
                info['tasks'].append(scheduled_task)
                info['scheduled_study_time'] += allocatable_time
                remaining_duration -= allocatable_time

                # Update available study time
                info['available_study_time'] = self.max_study_time_per_day - \
                                               info['scheduled_course_time'] - info['scheduled_study_time']

                date += timedelta(days=1)

            if remaining_duration > 0:
                warnings.warn(f"Warning: Unable to fully schedule task '{task.description}' before deadline.")

    def adjust_schedule_for_overloads(self):
        for date, info in self.schedule.items():
            total_scheduled_time = info['scheduled_course_time'] + info['scheduled_study_time']
            if total_scheduled_time > self.max_study_time_per_day:
                # Identify movable tasks (non-fixed, lower-priority tasks)
                movable_tasks = [task for task in info['tasks'] if not task.fixed_date and task.priority < 50]
                for task in movable_tasks:
                    # Try to move task to next available day
                    new_date = date + timedelta(days=1)
                    while new_date <= task.latest_end_date:
                        if new_date.weekday() not in self.study_days_per_week:
                            new_date += timedelta(days=1)
                            continue
                        new_info = self.schedule[new_date]
                        available_study_time = self.max_study_time_per_day - \
                                               new_info['scheduled_course_time'] - new_info['scheduled_study_time']
                        if available_study_time >= task.duration:
                            # Move task
                            info['tasks'].remove(task)
                            info['scheduled_study_time'] -= task.duration
                            new_info['tasks'].append(task)
                            new_info['scheduled_study_time'] += task.duration
                            # Update available study times
                            info['available_study_time'] += task.duration
                            new_info['available_study_time'] -= task.duration
                            break
                        new_date += timedelta(days=1)
                # Recalculate total scheduled time
                total_scheduled_time = info['scheduled_course_time'] + info['scheduled_study_time']
                if total_scheduled_time > self.max_study_time_per_day:
                    print(f"Note: Overload on {date}. Total scheduled time: {total_scheduled_time} hours.")

    def finalize_schedule(self):
        # Sort tasks on each date by start time
        for date, info in self.schedule.items():
            info['tasks'].sort(key=lambda x: (x.fixed_date, x.start_time if x.start_time else time(23, 59)))

    def generate_ical_file(self, filename):
        # Write to file
        with open(filename, 'wb') as f:
            ical = self.get_raw_ical()
            f.write(ical)

        print(f"iCalendar file '{filename}' generated successfully.")

    def get_schedule(self):
        # Return the schedule for display purposes
        return self.schedule

    def get_ical(self) -> icalendar.Calendar:
        cal = icalendar.Calendar()
        cal.add('prodid', '-//StudyScheduleGenerator//EN')
        cal.add('version', '2.0')

        for date, info in self.schedule.items():
            tasks = info['tasks']
            current_time = self.preferred_study_start
            for task in tasks:
                event = icalendar.Event()
                event.add('uid', str(uuid.uuid4()))
                event.add('dtstamp', datetime.now())

                # Determine event times
                if task.fixed_date:
                    event.add('dtstart', datetime.combine(date, task.start_time))
                    event.add('dtend', datetime.combine(date, task.end_time))
                else:
                    # Schedule within preferred study hours
                    start_time = current_time
                    end_time = (datetime.combine(date, start_time) + timedelta(hours=task.duration)).time()
                    if end_time > self.preferred_study_end:
                        # Adjust to preferred study hours
                        end_time = self.preferred_study_end
                        duration = (datetime.combine(date, end_time) -
                                    datetime.combine(date, start_time)).total_seconds() / 3600
                        if duration <= 0:
                            continue  # Cannot schedule, move to next task
                    else:
                        duration = task.duration
                    event.add('dtstart', datetime.combine(date, start_time))
                    event.add('dtend', datetime.combine(date, end_time))
                    # Update current_time
                    current_time = (
                            datetime.combine(date, end_time) + timedelta(minutes=5)).time()  # 5-minute gap

                event.add('summary', task.description)
                event.add('description', f"Course: {task.course_name}")
                cal.add_component(event)

        return cal

    def get_raw_ical(self) -> bytes:
        return self.get_ical().to_ical()
