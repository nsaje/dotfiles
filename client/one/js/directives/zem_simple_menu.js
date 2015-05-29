/*globals constants*/
"use strict";

oneApp.directive('zemSimpleMenu', function () {
    return {
        restrict: 'E',
        scope: {
            selectAll: '=',
            selectionOptions: '='
        },
        templateUrl: '/partials/zem_simple_menu.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
        	$scope.$watch('selectionOptions', function (val){
        		console.log('simpl');	
			});
        }]
    }
});
