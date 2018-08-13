require('./zemContentInsights.component.less');

angular.module('one.widgets').component('zemContentInsights', {
    bindings: {
        entity: '<',
    },
    template: require('./zemContentInsights.component.html'),
    controller: function(
        $scope,
        $element,
        $window,
        $timeout,
        zemNavigationNewService,
        zemContentInsightsEndpoint
    ) {
        var $ctrl = this;

        $ctrl.loading = true;

        $ctrl.$onChanges = function() {
            loadData();
        };

        function loadData() {
            if (!$ctrl.entity) return;

            zemContentInsightsEndpoint
                .getData($ctrl.entity)
                .then(function(data) {
                    $ctrl.data = data;
                    $ctrl.loading = false;
                });
        }
    },
});
