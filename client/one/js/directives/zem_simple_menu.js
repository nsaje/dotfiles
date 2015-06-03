"use strict";

oneApp.directive('zemSimpleMenu', function () {
    return {
        restrict: 'E',
        scope: {
            customSelectionOptions: '=',
			selectedOption: '=',
			selectedAllCheckbox: '='
        },
        templateUrl: '/partials/zem_simple_menu.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
			$scope.toggleDropdown = function (ev) {
				if (ev.target === null) { return; }
				if (ev.target.id === 'zem-all-checkbox') {
					// prevent events from leaving the checkbox and suppressing checkbox switch
					// very important switch - breaks the entire control if commented
					ev.stopPropagation();
					return;
				}
			};

			$scope.handleSelection = function(option) {
			    option.callback(option.name);
			};

			$scope.$watch('customSelectionOptions', function (newOption, oldOption) {
				console.log('Sprememba');
				console.log(newOption);
			}, true);

        }]
    };
});
