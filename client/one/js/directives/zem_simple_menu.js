/*globals constants*/
"use strict";

oneApp.directive('zemSimpleMenu', function () {
    return {
        restrict: 'E',
        scope: {
            id: '=',
            onChange: '=',
            isEditable: '=',
            value: '=',
            enabledValue: '=',
            pausedValue: '=',
            disabledMessage: '=',
            selectAll: '=',
            selectionOptions: '=selectionOptions'
        },
        templateUrl: '/partials/zem_simple_menu.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
        	// $scope.selectionOptions
        	// alert($scope.selectionOptions);

			$scope.$watch('selectionOptions', function (newValue, oldValue) {
				console.log(newValue);
			}, true);

            $scope.active = false;
            var setActive = function () {
                $scope.active = $scope.value === $scope.enabledValue;
            };
			
            $scope.dropdownToggle = function () {
			};

            $scope.selectAllCallback = function () {
			};

            $scope.setState = function (state) {
                $scope.isOpen = false;

                if (state === $scope.value) {
                    return;
                }

                $scope.value = state;
                setActive();

                $scope.onChange($scope.id, state);
            };

            setActive();
        }]
    }
});
