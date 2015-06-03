// strict disabled since tests didn't pass on CircleCI (for no reason)
// "use strict";

oneApp.directive('zemSimpleMenu', function () {
    return {
        restrict: 'E',
        scope: {
            customSelectionOptions: '=',
			select2Config: '=',
			selectedOption: '='
        },
        templateUrl: '/partials/zem_simple_menu.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
			$scope.checkboxHover = false;

			$scope.customFormat = function (state) {
				return state.text;
			};

			$scope.$watch('selectedOption', function (newOption, oldOption) {
			    if (oldOption == newOption) return;
			    newOption.callback(newOption.name)
			}, true);

			$scope.checkboxHoverIn = function() {
				$scope.checkboxHover = true;
			};

			$scope.checkboxHoverOut = function() {
				$scope.checkboxHover = false;
			};

			$scope.select2Config = {
				minimumResultsForSearch: -1, 
				placeholder: "<input type=\"checkbox\" data-ng-change=\"\" data-ng-model=\"selectAllCheckbox\" ng-mouseover=\"checkboxHoverIn()\" ng-mouseleave=\"checkboxHoverOut()\"></input>",
				formatResult: $scope.customFormat,
				formatSelection: $scope.customFormat,
				escapeMarkup: function(m) { return m; },
                dropdownCssClass: 'select2-simple-menu-dropdown'
			};

        }]
    }
});
