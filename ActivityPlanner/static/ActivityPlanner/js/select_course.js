const csrftoken = Cookies.get('csrftoken');
let last_id;
let current_division;
let autocomplete_courses = [];
let current_course, current_section_code;

$(document).ready(function () {
    $('.session-select').click(function (e) {
        let id = this.id;
        $.ajax({
            url: "/select_session/",
            headers: {'X-CSRFToken': csrftoken},
            type: "POST",
            data: {'session': id}
        }).done(function (resp) {
            $(`button#${last_id}`)
                .removeClass('btn-primary')
                .addClass('btn-outline-primary');

            $(`button#${id}`)
                .removeClass('btn-outline-primary')
                .addClass('btn-primary');

            last_id = id;
        });
    });

    getDivisions(function (divisions) {
        for (let division_name in divisions) {
            $("select#DivisionSelector")
                .append(`<option value="${divisions[division_name]}">${division_name}</option>`);
        }
    });

    $("select#DivisionSelector").on('change', function (a) {
        if (this.value === "") {
            $("input#courseInput")
                .prop('disabled', true)
                .attr('placeholder', "Please select a division");
        } else {
            $("input#courseInput")
                .prop('disabled', false)
                .attr('placeholder', "Please enter a course code");
        }
    });

    $("input#courseInput").on('input', function () {
        if (this.value.length === 2) {
            autocomplete_courses = [];
            current_division = $("select#DivisionSelector option:selected").val();
            autocompleteTerm(this.value, current_division, function (autocompleteOptions) {
                for (let courseCode in autocompleteOptions) {
                    autocomplete_courses.push(
                        `${courseCode} ${autocompleteOptions[courseCode].sectionCode}  ${autocompleteOptions[courseCode].name}`
                    );
                }
                $("input#courseInput").autocomplete({
                    source: autocomplete_courses
                });
            })
        }
    });
    $("button#searchCourse").on('click', function (a) {
        let append_html = ``;
        current_course = $("input#courseInput").val().split(' ');
        current_division = $("select#DivisionSelector option:selected").val();
        if (current_course.length > 1)
            current_section_code = current_course[1];
        else
            current_section_code = '';

        searchCourse(
            csrftoken,
            current_course[0],
            current_section_code,
            current_division,
            function (statusCode, result) {
                let course_info = result.pageableCourse.courses.courses;
                let courses = course_info.sections.sections;
                let course_code = course_info.code;
                let course_title = course_info.name;

                append_html += `
                            <h1>Search Result:</h1>
                            <h2>${course_code}: ${course_title}</h2>
                        `;

                for (let i = 0; i < courses.length; i++) {
                    let meetingTimes;
                    if (!courses[i].meetingTimes)
                        meetingTimes = {
                            'start': {'day': 0, 'millisofday': 0},
                            'end': {'day': 0, 'millisofday': 0},
                            'building': {'buildingUrl': "", "buildingCode": "ZZ"}
                        };
                    else
                        meetingTimes = courses[i].meetingTimes.meetingTimes;

                    let meetingTimeString = ``;
                    if (meetingTimes.constructor === Array) {
                        meetingTimeString += `<p class="mb-1">Meeting time:</p>`
                        for (let i = 0; i < meetingTimes.length; i++) {
                            meetingTimeString += `
                                        <p class="mb-1">&emsp;${convertToWeekday(parseInt(meetingTimes[i].start.day))}, ${millisecondsToTime(meetingTimes[i].start.millisofday)}~${millisecondsToTime(meetingTimes[i].end.millisofday)}</p>`
                        }
                        meetingTimeString += `Building: <a href="${meetingTimes[0].building.buildingUrl}">${meetingTimes[0].building.buildingCode}</a>`;
                    } else {
                        meetingTimeString = `
                                    <p class="mb-1">Meeting time: ${convertToWeekday(parseInt(meetingTimes.start.day))}, ${millisecondsToTime(meetingTimes.start.millisofday)}~${millisecondsToTime(meetingTimes.end.millisofday)}</p>
                                    Building: <a href="${meetingTimes.building.buildingUrl}">${meetingTimes.building.buildingCode}</a>
                                `;
                    }

                    append_html += `
                                <div class="list-group-item list-group-item-action" aria-current="true">
                                    <div class="w-100 form-check">
                                        <input class="form-check-input time-selection" type="checkbox" value="" id="${courses[i].name}">
                                        <h5 class="mb-1">${courses[i].name}</h5>
                                        <small>${courses[i].type}</small>
                                        ${meetingTimeString}
                                    </div>
                                </div>
                            `;
                }
                $("div#submitSchedule").css("display", "block");
                $("div#result-area").append(append_html);
            }
        );

        $("button#submitButton").on('click', function (a) {
            console.log($("#input.time-selection:checked"));
        })
    })
})
