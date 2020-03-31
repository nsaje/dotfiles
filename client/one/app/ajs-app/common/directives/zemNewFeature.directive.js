angular.module('one.common').directive('zemNewFeature', function() {
    return {
        restrict: 'A',
        scope: false,
        link: function(scope, element, attrs) {
            attrs.$observe('zemNewFeature', function(value) {
                removeNewFeatureElement(element);

                if (value === 'true') {
                    appendNewFeatureElement(
                        element,
                        attrs.zemNewFeatureClass || ''
                    );
                }
            });
        },
    };

    function removeNewFeatureElement(element) {
        angular
            .element(element)
            .find('.zem-new-feature')
            .remove();
    }

    function appendNewFeatureElement(element, newFeatureClass) {
        var newFeatureHtml =
            '<div class="zem-new-feature ' +
            newFeatureClass +
            '"><i class="zem-new-feature__text">NEW</i></div>';

        angular.element(element).append(newFeatureHtml);
    }
});
