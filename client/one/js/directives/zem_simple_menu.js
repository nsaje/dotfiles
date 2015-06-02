/*globals constants*/
"use strict";

oneApp.directive('zemSimpleMenu', function () {
    return {
        restrict: 'E',
        scope: {
            selectAll: '=',
            selectionOptions: '=',
			select2Config: '=',
			selection: '='
        },
        templateUrl: '/partials/zem_simple_menu.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
			$scope.checkboxHover = false;

			$scope.customFormat = function (state) {
				return state.text;
			};

			$scope.$watch('selection', function (newOption, oldOption) {
			    if (oldOption == newOption) return;
			    newOption.callback(newOption.name)
			}, true);

			$scope.changeCallback = function () {
				console.log($scope.selection);
			};

			$scope.checkboxSelectionCallback = function(ev) {
				console.log(ev);
			};

			$scope.checkboxHoverIn = function() {
				$scope.checkboxHover = true;
				console.log($scope.checkboxHover);
			};

			$scope.checkboxHoverOut = function() {
				$scope.checkboxHover = false;
				console.log($scope.checkboxHover);
			};

			$scope.select2Config = {
				minimumResultsForSearch: -1, 
				dropdownCssClass: 'show-rows',
				placeholder: "<input type=\"checkbox\" data-ng-change=\"\" data-ng-model=\"selectAllCheckbox\" ng-mouseover=\"checkboxHoverIn()\" ng-mouseleave=\"checkboxHoverOut()\"></input>",
				formatResult: $scope.customFormat,
				formatSelection: $scope.customFormat,
				escapeMarkup: function(m) { return m; },
                dropdownCssClass: 'select2-simple-menu-dropdown'
			};

        }]
    }
});
