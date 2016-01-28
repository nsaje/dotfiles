/* globals oneApp */
'use strict';

oneApp.directive('zemDropdown', function () {
    return {
        restrict: 'E',
        scope: {
            placeholder: '@zemPlaceholder',
            disabledTitle: '@zemDisabledTitle',
            onSelect: '&zemOnSelect',
            checkDisabled: '&zemCheckDisabled',
            dropdownOptions: '=zemDropdownOptions',
            dropdownCssClass: '@zemDropdownCssClass',
            cssClass: '@zemCssClass',
            noMatchesPlaceholder: '@zemNoMatchesPlaceholder'
        },
        templateUrl: '/partials/zem_dropdown.html',
        controller: ['$scope', '$compile', '$element', '$attrs', function ($scope, $compile, $element, $attrs) {
            var formatSelection = function (object) {
                var option;
                $scope.dropdownOptions.forEach(function (item) {
                    if (item.value == object.id) {
                        option = item;
                    }
                });
                var notification = option.notification;
                var element = angular.element(document.createElement('div'));
                if (notification) {
                    element.attr('popover', notification);
                    element.attr('popover-trigger', 'mouseenter');
                    element.attr('popover-placement', 'right');
                    element.attr('popover-append-to-body', 'true');

                    // hide immediately without animation - solves a glitch when
                    // the element is selected
                    element.attr('popover-animation', 'false');
                    element.on('$destroy', function () {
                        element.trigger('mouseleave');
                    });
                }

                element.text(object.text);

                if (option.internal) {
                    var internal = $compile(angular.element(document.createElement('zem-internal-feature')))($scope);
                    element.append(internal);
                }

                return $compile(element)($scope);
            };

            $scope.dropdownConfig = {
                minimumResultsForSearch: -1,
                dropdownCssClass: $scope.dropdownCssClass,
                formatNoMatches: $scope.noMatchesPlaceholder,
                formatResult: formatSelection
            };

            $scope.selectedItem = null;

            $scope.callOnSelect = function () {
                $scope.onSelect({selected: $scope.selectedItem});
                $scope.selectedItem = null;
            };

            $scope.$watch('checkDisabled()', function (newValue, oldValue) {
                $scope.disabledTitleOrUndefined = $scope.checkDisabled() ? $scope.disabledTitle : undefined;
            });
        }]
    };
});
