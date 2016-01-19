/*globals oneApp,$*/
oneApp.directive('zemMultiselect', [function () {
    return function (scope, element, attributes) {

        element = $(element[0]); // Get the element as a jQuery element

        element.multiselect({
            includeSelectAllOption: true,
            enableCaseInsensitiveFiltering: true,
            maxHeight: 190

        });

        // Watch for any changes to the length of our select element
        scope.$watch(function () {
            return element[0].length;
        }, function () {
            element.multiselect('rebuild');
        });

        // Watch for any changes from outside the directive and refresh
        scope.$watch(attributes.ngModel, function () {
            element.multiselect('refresh');
        });
    };
}]);
