oneApp.directive('zemSelect2ModelTransform', ['$compile', function($compile) {
    return { 
        restrict: 'A',
        require: 'ngModel',
        link: function(scope, element, attr, ngModel) {
            if (!ngModel) {
                return;
            }

            ngModel.$parsers.push(function (value) {
                return value ? value.id : '';
            });

            ngModel.$formatters.push(function (value) {
                var text = isNaN(value) ? '' : value + '%';
                return {id: value, text: text};
            });
        }
    };
}]);
