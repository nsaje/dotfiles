/*globals constants*/
"use strict";

oneApp.directive('zemSimpleMenu', function () {
    return {
        restrict: 'E',
        scope: {
            selectAll: '=',
            selectionOptions: '=',
			select2Config: '='
        },
        templateUrl: '/partials/zem_simple_menu.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
			$scope.customFormat = function (state, container) {
				console.log(state);
				var fontColor = 'Purple';
				return  "<span style='color:" + fontColor + "'>" + state.text + "</span>";
			};

			$scope.select2Config = {
				minimumResultsForSearch: -1, 
				dropdownCssClass: 'show-rows',
				formatResult: $scope.customFormat,
				formatSelection: $scope.customFormat
			};
        }]
    }
});
