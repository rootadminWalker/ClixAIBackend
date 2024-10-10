const REFERENCE_API = '/api_ttb_get_division/'
const AUTOCOMPLETE_API = '/api_ttb_autocomplete_input/'
const SEARCH_API = '/api_ttb_search_times/'

function getDivisions(callback) {
    let divisions = {};
    $.ajax({
        url: REFERENCE_API,
        method: 'GET',
    }).done(function (result) {
        result = result.payload.divisions.divisions;
        for (let i = 0; i < result.length; i++) {
            divisions[result[i].label] = result[i].value;
        }
        callback(divisions);
    });
}

function autocompleteTerm(term, division, callback) {
    let autocompleteOptions = {};
    $.ajax({
        url: AUTOCOMPLETE_API,
        method: 'GET',
        data: {'term': term, "division": division}
    }).done(function (result) {
        let autocompleteOption = {};
        if (result.payload.codesAndTitles) {
            for (let i = 0; i < result.payload.codesAndTitles.codesAndTitles.length; i++) {
                autocompleteOption = result.payload.codesAndTitles.codesAndTitles[i];
                autocompleteOptions[autocompleteOption.code] = {
                    'sectionCode': autocompleteOption.sectionCode,
                    'name': autocompleteOption.name
                }
            }
        }
        callback(autocompleteOptions);
    })
}

function searchCourse(csrftoken, code, sectionCode, division, callback) {
    $.ajax({
        url: SEARCH_API,
        method: 'POST',
        headers: {'X-CSRFToken': csrftoken},
        data: {
            "courseCode": code,
            "courseSectionCode": sectionCode,
            'division': division
        },

    }).done(function (result) {
        callback(result.status.status.code, result.payload);
    });
}

function millisecondsToTime(milliseconds) {
    // Calculate hours, minutes, and seconds from milliseconds
    let hours = Math.floor(milliseconds / 3600000);
    let minutes = Math.floor((milliseconds % 3600000) / 60000);

    // Format the time as HH:MM:SS
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
}

function convertToWeekday(number) {
    switch (number) {
        case 1:
            return 'Monday';
        case 2:
            return 'Tuesday';
        case 3:
            return 'Wednesday';
        case 4:
            return 'Thursday';
        case 5:
            return 'Friday';
        case 6:
            return 'Saturday';
        case 7:
            return 'Sunday';
        default:
            return 'Invalid weekday number';
    }
}
