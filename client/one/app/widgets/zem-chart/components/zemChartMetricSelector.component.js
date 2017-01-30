angular.module('one.widgets').component('zemChartMetricSelector', {
    bindings: {
        chart: '<',
        metric: '<',
        nullable: '<',
        onMetricChanged: '&'
    },
    templateUrl: '/app/widgets/zem-chart/components/zemChartMetricSelector.component.html',
    controller: function () {
        var $ctrl = this;

        $ctrl.onChanged = function (metric) {
            $ctrl.onMetricChanged({value: metric});
        };
    }
});
