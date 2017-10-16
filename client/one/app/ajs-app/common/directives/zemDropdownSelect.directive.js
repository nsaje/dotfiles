angular.module('one.common').directive('zemDropdownSelect', function () {
    return {
        restrict: 'E',
        scope: {
            placeholder: '@zemPlaceholder',
            disabledTitle: '@zemDisabledTitle',
            onSelect: '&zemOnSelect',
            checkDisabled: '&zemCheckDisabled',
            dropdownOptions: '=zemDropdownSelectOptions',
            dropdownCssClass: '@zemDropdownSelectCssClass',
            cssClass: '@zemCssClass',
            noMatchesPlaceholder: '@zemNoMatchesPlaceholder'
        },
        template: require('./zemDropdownSelect.directive.html'),
        controller: function ($scope, $compile) {
            var formatSelection = function (object) {
                var option;
                $scope.dropdownOptions.forEach(function (item) {
                    if (item.value == object.id) { // eslint-disable-line eqeqeq
                        option = item;
                    }
                });
                var notification;
                var element = angular.element(document.createElement('div'));
                if (option.notificationDisabled && object.disabled) {
                    notification = option.notificationDisabled;
                } else {
                    notification = option.notification;
                }
                if (notification) {
                    element.attr('zem-lazy-popover-text', notification);
                    element.attr('zem-lazy-popover-trigger', 'mouseenter');
                    element.attr('zem-lazy-popover-placement', 'right');
                    element.attr('zem-lazy-popover-append-to-body', 'true');

                    // hide immediately without animation - solves a glitch when
                    // the element is selected
                    element.attr('zem-lazy-popover-animation', 'false');
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

            $scope.$watch('checkDisabled()', function () {
                $scope.disabledTitleOrUndefined = $scope.checkDisabled() ? $scope.disabledTitle : undefined;
            });
        }
    };
});
