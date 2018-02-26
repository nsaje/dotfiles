$(function() {
    $(document).ready(function() {
        initDaypartingWidget($("#id_dayparting"));
    });
});


var initDaypartingWidget = function(sourceInputField) {
    const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const DAY_FIELDS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];

    var isMouseDown = false;
    var isMouseDownEveryDay = false;
    var doHighlight = false;
    var doHighlightEveryDay = false;
    var daypartingTable = null;
    var daypartingTableEveryDay = null;
    var daypartingTimezoneSelect = null;

    var state = null;
    var stateBackup = null;

    $(document).mouseup(function() {
        isMouseDown = false;
        isMouseDownEveryDay = false;
    });

    initWidget(sourceInputField);
    state = JSON.parse($(sourceInputField).val());
    stateBackup = $.extend(true, {}, state);  // clone
    setState(state);

    function setDayHour(day, hour, isSelected) {
        if (state[day] === undefined) {
            state[day] = [];
        }
        var idx = state[day].indexOf(hour);
        if (isSelected && idx == -1) {
            state[day].push(hour);
            state[day].sort();
        }
        if (!isSelected && idx > -1) {
            state[day].splice(idx, 1);
        }
        if (!state[day].length) {
            delete state[day];
        }
        stateChanged();
    }

    function setEveryDayHour(hour, isSelected) {
        for (var i = 0; i < DAY_FIELDS.length; i++) {
            setDayHour(DAY_FIELDS[i], hour, isSelected);
        }
        stateChanged();
    }

    function setTimezone(timezone) {
        state['timezone'] = timezone;
        stateChanged();
    }

    function setState(newState) {
        state = newState;
        stateChanged();
    }

    function stateChanged() {
        renderState();
        sourceInputField.val(JSON.stringify(state, null, 2));
    }


    function initWidget() {
        var daypartingWidget = $("<div id='daypartingWidget'></div>");

        daypartingTable = createTable();
        daypartingTableEveryDay = createTableEveryDay();
        daypartingTimezoneSelect = $("<select id='daypartingTimezoneSelect'></select>");
        daypartingTimezoneSelect.append(
            $("<option></option>")
                .attr('value', '')
                .text("User's timezone"));
        for (var i = 0; i < DAYPARTING_TIMEZONES.length; i++) {
            var option = $("<option></option>")
                .attr('value', DAYPARTING_TIMEZONES[i])
                .text(DAYPARTING_TIMEZONES[i]);
            daypartingTimezoneSelect.append(option);
        }
        daypartingTimezoneSelect.change(function() {
            setTimezone($(this, 'option:selected').val());
        });
        var discardButton = $("<button></button>").text('Discard changes');
        discardButton.click(onDiscard);
        var resetButton = $("<button></button>").text('Reset dayparting');
        resetButton.click(onReset);

        daypartingWidget.append(daypartingTimezoneSelect);
        daypartingWidget.append(daypartingTable);
        daypartingWidget.append(daypartingTableEveryDay);
        daypartingWidget.append(discardButton);
        daypartingWidget.append(resetButton);

        daypartingWidget.insertBefore(sourceInputField);
        sourceInputField.hide();
    }

    function onDiscard(e) {
        e.preventDefault();
        var initialState = $.extend(true, {}, stateBackup);  // clone
        setState(initialState);
        return false;
    }

    function onReset(e) {
        e.preventDefault();
        if (confirm("Are you sure you want to reset dayparting?")) {
            setState({});
        }
        return false;
    }

    function createTable() {
        var daypartingTable = $("<table id='daypartingTable'></table>");

        var headerRow = $("<tr></tr>");
        for (var hour = -1; hour < 24; hour++) {
            var cell = $("<td></td>");
            if (hour > -1) {
                cell.text(hour);
            }
            headerRow.append(cell);
        }
        daypartingTable.append(headerRow);

        for (var day = 0; day < DAYS.length; day++) {
            var row = $("<tr class='daypartingDay'></tr>");
            var headerCell = $("<td></td>");
            headerCell.text(DAYS[day]);
            row.append(headerCell);

            for (var hour = 0; hour < 24; hour++) {
                var cell = $("<td class='daypartingHour'></td>");
                cell.data('day', DAY_FIELDS[day]);
                cell.data('hour', hour);
                cell
                    .mousedown(function() {
                        isMouseDown = true;
                        doHighlight = ! $(this).hasClass("highlighted");
                        onCellMouseDown($(this));
                        return false;  // prevent text selection
                    })
                    .mouseover(function() {
                        if (isMouseDown) {
                            onCellMouseDown($(this));
                        }
                    });
                row.append(cell);
            }
            daypartingTable.append(row);
        }
        return daypartingTable;
    }

    function onCellMouseDown(cell) {
        var day = $(cell).data('day');
        var hour = $(cell).data('hour');
        setDayHour(day, hour, doHighlight);
    }

    function createTableEveryDay() {
        var daypartingTableEveryDay = $("<table id='daypartingTableEveryDay'></table>");

        var row = $("<tr></tr>");
        var headerCell = $("<td></td>");
        headerCell.text("Every Day");
        row.append(headerCell);

        for (var hour = 0; hour < 24; hour++) {
            var cell = $("<td class='daypartingHour'></td>");
            cell.data('hour', hour);
            cell
                .mousedown(function() {
                    isMouseDownEveryDay = true;
                    doHighlightEveryDay = ! $(this).hasClass("highlighted");
                    onEverydayCellMouseDown($(this));
                    return false;  // prevent text selection
                })
                .mouseover(function() {
                    if (isMouseDownEveryDay) {
                        onEverydayCellMouseDown($(this));
                    }
                });
            row.append(cell);
        }
        daypartingTableEveryDay.append(row);
        return daypartingTableEveryDay;
    }

    function onEverydayCellMouseDown(cell) {
        var hour = $(cell).data('hour');
        setEveryDayHour(hour, doHighlightEveryDay);
    }

    function renderState() {
        var dayparting = state;
        var tableError = new Error('Dayparting table incorrectly constructed, contact engineering');
        var dayRows = daypartingTable.find('.daypartingDay');
        if (dayRows.length != 7) {
            throw tableError;
        }
        for (var day = 0; day < dayRows.length; day++) {
            var hourCells = $(dayRows[day]).find('.daypartingHour');
            if (hourCells.length != 24) {
                throw tableError;
            }

            if (!dayparting[DAY_FIELDS[day]]) {
                hourCells.removeClass('highlighted');
                continue;
            }

            for (var hour = 0; hour < hourCells.length; hour++) {
                if (dayparting[DAY_FIELDS[day]].indexOf(hour) > -1) {
                    $(hourCells[hour]).addClass('highlighted');
                } else {
                    $(hourCells[hour]).removeClass('highlighted');
                }
            }
        }

        var everyDayCells = daypartingTableEveryDay.find('.daypartingHour');
        for (var hour = 0; hour < everyDayCells.length; hour++) {
            var allDaysHaveHour = true;
            for (var day = 0; day < DAY_FIELDS.length; day++) {
                var dayConfig = dayparting[DAY_FIELDS[day]] || [];
                var dayHasHour = dayConfig.indexOf(hour) > -1;
                allDaysHaveHour = allDaysHaveHour && dayHasHour;
            }
            if (allDaysHaveHour) {
                $(everyDayCells[hour]).addClass('highlighted');
            } else {
                $(everyDayCells[hour]).removeClass('highlighted');
            }
        }

        var timezone = dayparting['timezone'] || '';
        daypartingTimezoneSelect.val(timezone);
    }
}
