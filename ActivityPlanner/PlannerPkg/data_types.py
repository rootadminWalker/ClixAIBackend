# Data classes
class StudyTask:
    def __init__(self, description, course_name, duration, earliest_start_date,
                 latest_end_date, fixed_date=False, start_time=None, end_time=None,
                 priority=0, splittable=True, total_duration=None):
        self.description = description
        self.course_name = course_name
        self.duration = duration  # Duration for this instance
        self.earliest_start_date = earliest_start_date
        self.latest_end_date = latest_end_date
        self.fixed_date = fixed_date
        self.start_time = start_time
        self.end_time = end_time
        self.priority = priority
        self.splittable = splittable
        self.total_duration = total_duration  # For assignments
        self.remaining_duration = total_duration if total_duration else duration


class CourseEvent:
    def __init__(self, event_type, course_name, description, date, start_time, end_time):
        self.event_type = event_type  # Lecture, Tutorial, Lab, Assessment
        self.course_name = course_name
        self.description = description
        self.date = date
        self.start_time = start_time
        self.end_time = end_time


class Assignment:
    def __init__(self, assignment_name, course_name, deadline, estimated_duration, suggested_start_time):
        self.assignment_name = assignment_name
        self.course_name = course_name
        self.deadline = deadline
        self.estimated_duration = estimated_duration
        self.suggested_start_time = suggested_start_time


class Assessment:
    def __init__(self, assessment_name, course_name, deadline):
        self.assessment_name = assessment_name
        self.course_name = course_name
        self.deadline = deadline


class Course:
    def __init__(self, course_name):
        self.course_name = course_name
        self.lectures = []  # List of CourseEvent
        self.tutorials = []  # List of CourseEvent
        self.labs = []  # List of CourseEvent
        self.assignments = []  # List of Assignment
        self.assessments = []  # List of Assessment

    def add_event(self, event: CourseEvent):
        event_type = event.event_type
        if event_type == 'Lecture':
            self.lectures.append(event)
        elif event_type == 'Tutorial':
            self.tutorials.append(event)
        elif event_type == 'Lab':
            self.labs.append(event)
