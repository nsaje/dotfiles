/*globals angular,moment*/

/**
 * @license ng-bs-daterangepicker v0.0.1
 * (c) 2013 Luis Farzati http://github.com/luisfarzati/ng-bs-daterangepicker
 * License: MIT
 */

/* THIS IS A MODIFIED VERSION, DO NOT REPLACE WITH A STOCK VERSION */
(function (angular) {
    function addLabelsToCalendar(picker) {
        if (angular.element(picker).find('.calendar.left .calendar-date tbody .calendar-label').length) {
            return;
        }
        angular.element(picker)
            .find('.calendar.left .calendar-date tbody')
            .append('<tr><td colspan="7" class="calendar-label">start date</td></tr>');
        angular.element(picker)
            .find('.calendar.right .calendar-date tbody')
            .append('<tr><td colspan="7" class="calendar-label">end date</td></tr>');
    }
    'use strict';
    angular.module('ngBootstrap', []).directive('input', ['$compile', '$parse', function ($compile, $parse) {
        return {
            restrict: 'E',
            require: '?ngModel',
            link: function ($scope, $element, $attributes, ngModel) {
                if ($attributes.type !== 'daterange') {
                    return;
                }

                var options = {};
                options.format = $attributes.format || 'YYYY-MM-DD';
                options.separator = $attributes.separator || ' - ';
                options.minDate = $attributes.minDate && moment($attributes.minDate);
                options.maxDate = $attributes.maxDate && moment($attributes.maxDate);
                options.dateLimit = $attributes.limit && moment.duration.apply(
                    this, $attributes.limit.split(' ').map(
                        function (elem, index) {
                            return (index === 0 && parseInt(elem, 10)) || elem;
                        })
                    );
                options.ranges = $attributes.ranges && $parse($attributes.ranges)($scope);
                options.applyClass = 'btn-primary';
                options.opens = 'left';

                function format(date) {
                    return date.format(options.format);
                }

                function formatted(dates) {
                    return [format(dates.startDate), format(dates.endDate)].join(options.separator);
                }

                function dateRangeChanged(start, end) {
                    $scope.$apply(function () {
                        ngModel.$setViewValue({ startDate: start, endDate: end });
                        ngModel.$render();
                    });
                }

                ngModel.$formatters.unshift(function (modelValue) {
                    if (!modelValue) {
                        return '';
                    }
                    return modelValue;
                });

                ngModel.$parsers.unshift(function (viewValue) {
                    return viewValue;
                });

                ngModel.$render = function () {
                    if (!ngModel.$viewValue || !ngModel.$viewValue.startDate) {
                        return;
                    }
                    $element.val(formatted(ngModel.$viewValue));
                };

                $attributes.$observe('maxDate', function(newValue, oldValue) {
                    if (newValue) {
                        options.maxDate = $attributes.maxDate && moment($attributes.maxDate);
                        $element.data('daterangepicker').setOptions(options, dateRangeChanged);
                    }
                });

                $attributes.$observe('ranges', function(newValue, oldValue) {
                    if (newValue) {
                        options.ranges = $attributes.ranges && $parse($attributes.ranges)($scope);
                        angular.forEach(options.ranges, function (value, key) {
                            options.ranges[key] = [moment(value[0]), moment(value[1])];
                        });
                        $element.data('daterangepicker').setOptions(options, dateRangeChanged);
                    }
                });

                $scope.$watch($attributes.ngModel, function (modelValue) {
                    if (!modelValue || (!modelValue.startDate)) {
                        ngModel.$setViewValue({ startDate: moment().startOf('day'), endDate: moment().startOf('day') });
                        return;
                    }
                    $element.data('daterangepicker').startDate = modelValue.startDate;
                    $element.data('daterangepicker').endDate = modelValue.endDate;
                    $element.data('daterangepicker').updateView();
                    $element.data('daterangepicker').updateCalendars();
                    $element.data('daterangepicker').updateInputText();
                });

                $element.daterangepicker(options, dateRangeChanged);
                $element.on('show.daterangepicker', function (ev, picker) {
                    addLabelsToCalendar(picker.container);
                });
                angular.element(window.document).on('click', '.calendar-date .available', function () {
                    angular.element(this).parent('.calendar-date').promise().done(function () {
                        addLabelsToCalendar('.daterangepicker.show-calendar');
                    });
                });
            }
        };
    }]);
}(angular));

