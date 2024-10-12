import json
from datetime import timedelta

import requests
import xmltodict
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

import ActivityPlanner.PlannerPkg.utils as utils
from ActivityPlanner.PlannerPkg.data_types import Assignment, Assessment
from ActivityPlanner.PlannerPkg.data_types import CourseEvent, Course
from ActivityPlanner.PlannerPkg.scheduler_generator import BetaStudyScheduleGenerator
from ActivityPlanner.PlannerPkg.utils import get_closest_event_start_date

REFERENCE_API = 'https://api.easi.utoronto.ca/ttb/reference-data/'
# Term, Divisions
AUTOCOMPLETE_API = 'https://api.easi.utoronto.ca/ttb/getOptimizedMatchingCourseTitles?term={}&divisions={}&sessions=Fall-Winter&sessions=20249&sessions=20251&sessions=20249-20251&lowerThreshold=50&upperThreshold=200'
SEARCH_API = 'https://api.easi.utoronto.ca/ttb/getPageableCourses'

todos = [
    {
        'head': 'List group item heading 1',
        'due': 'In 3 days',
        'placeholder': 'Some placeholder content in a paragraph.',
        'print': 'A small print'
    },
    {
        'head': 'List group item heading 2',
        'due': 'In 2 days',
        'placeholder': 'Some placeholder content in a paragraph.',
        'print': 'A small print'
    },
    {
        'head': 'List group item heading 3',
        'due': 'In 1 days',
        'placeholder': 'Some placeholder content in a paragraph.',
        'print': 'A small print'
    }
]


# Create your views here.
def index(request):
    context = {
        'todos': todos
    }
    return render(request, 'ActivityPlanner/index.html', context=context)


def login(request):
    return HttpResponse('<h2>Hi motherfucker!</h2>')


def select_course(request):
    if request.method == 'POST':
        print(request.POST)
        return JsonResponse({'proceed': True})

    return render(request, 'ActivityPlanner/select_course.html')


@csrf_exempt
def generate_study_schedule(request):
    """
    {
        "semester_start": ("YYYY-MM-DD"),
        "semester_end": ("YYYY-MM-DD"),
        "preferred_study_start": (millisecs),
        "preferred_study_end": (millisecs),
        "study_level": ("Basic" or "Norma"l or "Advanced" or ''),
        "courses": {
            "(Course code ex. CSC108H5)": {
                "course_events": [
                    {
                        "type": ("Lecture" or "Lab" or "Tutorial"),
                        "session": (name of session, ex. "LEC101"),
                        "times": [{"day": (0, 1, 2....), "start": (millisecs), "end": (millisecs)}...]
                    }...
                ],
                "deadline_events": [
                    {
                        "name": (name of event, ex. A1, TT2, P3),
                        "type": ("Assignment" or "Practise" or "Assessment"),
                        "deadline": {"date": ("YYYY-MM-DD"), "time": (millisecs)},
                        "estimated_finish_time": (hours),  # If type is Assignment or Practise,
                        "suggested_start_date": ("YYYY-MM-DD")  # TODO: Will be deprecated
                    }...
                ]
            }, ...
        }
    }
    """
    if request.method == 'POST':
        events = json.loads(request.body)
        print(events)

        semester_start_date = utils.str_date_to_datetime(events['semester_start'])
        semester_end_date = utils.str_date_to_datetime(events['semester_end'])
        preferred_study_start = utils.milliseconds_to_time(events['preferred_study_start'])
        preferred_study_end = utils.milliseconds_to_time(events['preferred_study_end'])
        study_level = events['study_level']

        courses = []

        # Convert all events to self-defined types
        for course_name, events in events['courses'].items():
            course = Course(course_name)
            # Loop over all course events
            for course_event in events['course_events']:
                for course_time in course_event['times']:
                    # Convert string weekday to idx
                    event_weekday = utils.str_weekday_to_idx(course_time['day'])
                    # Get the closest event weekday to the semester start date
                    event_start_date = get_closest_event_start_date(event_weekday, semester_start_date)

                    # Convert time back to datetime format
                    start_time = utils.milliseconds_to_time(course_time['start'])
                    end_time = utils.milliseconds_to_time(course_time['end'])

                    # Starting from the event_start_date, add this course event weekly
                    delta_days = (semester_end_date - event_start_date).days + 1
                    for i in range(0, delta_days, 7):
                        date = event_start_date + timedelta(days=i)
                        event_type = course_event['type']
                        event = CourseEvent(
                            event_type=event_type,
                            course_name=course_name,
                            description=course_event['session'],
                            date=date,
                            start_time=start_time,
                            end_time=end_time
                        )
                        course.add_event(event)

            # Loop over all deadline events
            for deadline_event in events['deadline_events']:
                deadline_date = utils.str_date_to_datetime(deadline_event['deadline']['date'])
                deadline_date += timedelta(milliseconds=deadline_event['deadline']['time'])

                if deadline_event['type'] in ["Assignment", "Practise"]:
                    suggested_start_date = utils.str_date_to_datetime(deadline_event['suggested_start_date'])
                    course.assignments.append(Assignment(
                        assignment_name=deadline_event['name'],
                        course_name=course_name,
                        deadline=deadline_date,
                        estimated_duration=deadline_event['estimated_finish_time'],
                        suggested_start_time=suggested_start_date,
                    ))
                elif deadline_event['type'] == "Assessment":
                    course.assessments.append(Assessment(
                        assessment_name=deadline_event['name'],
                        course_name=course_name,
                        deadline=deadline_date,
                    ))

            courses.append(course)

        # Generate study schedule
        scheduler = BetaStudyScheduleGenerator(
            courses=courses,
            study_level=study_level,
            preferred_study_start=preferred_study_start,
            preferred_study_end=preferred_study_end,
            semester_start_date=semester_start_date,
            semester_end_date=semester_end_date
        )
        scheduler.generate_schedule()
        schedule = scheduler.get_raw_ical()

        return HttpResponse(schedule)


def api_ttb_get_division(request):
    if request.method == 'GET':
        divisions = requests.get(REFERENCE_API)
        divisions = xmltodict.parse(divisions.text)['TTBResponse']
        return JsonResponse(divisions)


def api_ttb_autocomplete_input(request):
    if request.method == 'GET':
        autocomplete_result = requests.get(
            AUTOCOMPLETE_API.format(request.GET['term'], request.GET['division'])
        )
        return JsonResponse(xmltodict.parse(autocomplete_result.text)['TTBResponse'])


def api_ttb_search_times(request):
    if request.method == 'POST':
        payload = {
            "courseCodeAndTitleProps": {
                "courseCode": '',
                "courseTitle": '',
                "courseSectionCode": '',
                "searchCourseDescription": False
            },
            "departmentProps": [],
            "campuses": [],
            "sessions": ["20249", "20251", "20249-20251"],
            "requirementProps": [],
            "instructor": "",
            "courseLevels": [],
            "deliveryModes": [],
            "dayPreferences": [],
            "timePreferences": [],
            "divisions": [],
            "creditWeights": [],
            "availableSpace": False,
            "waitListable": False,
            "page": 1,
            "pageSize": 100,
            "direction": "asc"
        }
        data = request.POST.dict()
        payload['courseCodeAndTitleProps']['courseCode'] = data['courseCode']
        payload['courseCodeAndTitleProps']['courseSectionCode'] = data['courseSectionCode']
        payload['divisions'].append(data['division'])

        search_result = requests.post(SEARCH_API, json=payload)
        return JsonResponse(xmltodict.parse(search_result.text)['TTBResponse'])
