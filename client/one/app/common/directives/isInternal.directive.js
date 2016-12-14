angular.module('one.common').directive('isInternal', function (zemPermissions) {
    var INTERNAL_FEATURE_HTML = '<i class="internal-feature"></i>';
    return {
        restrict: 'A',
        scope: false,
        priority: -999999,
        compile: function (tElement, tAttrs) {
            if (zemPermissions.isPermissionInternal(tAttrs.isInternal)) {
                angular.element(tElement).prepend(INTERNAL_FEATURE_HTML);
            }
        }
    };
});
