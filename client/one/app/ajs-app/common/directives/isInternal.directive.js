angular.module('one.common').directive('isInternal', function(zemAuthStore) {
    var INTERNAL_FEATURE_HTML = '<i class="internal-feature"></i>';
    return {
        restrict: 'A',
        scope: false,
        link: function(scope, element, attrs) {
            if (
                attrs.isInternal === 'true' ||
                zemAuthStore.isPermissionInternal(attrs.isInternal)
            ) {
                angular.element(element).prepend(INTERNAL_FEATURE_HTML);
            }
        },
    };
});
