'use strict'

describe('zemChart', function () {
    var scope, chart, isolate;
    var data = [{
        id: 'totals',
        name: 'Totals',
        seriesData: {
            cost: [
                ['2014-07-10', 205.1312],
                ['2014-07-11', 128.5189]
            ]
        }
    }];

    beforeEach(module('one'));

    beforeEach(inject(function ($rootScope, $compile) {
        scope = $rootScope.$new();

        chart = '<zem-chart zem-data="chartData" zem-metric1="chartMetric1" zem-metric2="chartMetric2" zem-metric-options="chartMetricOptions" zem-min-date="startDate" zem-max-date="endDate"></zem-chart>';

        scope.chartMetric1 = 'cost';
        scope.chartMetricOptions = [{name: 'Spend', value: 'cost'}];
        scope.startDate = moment('2014-07-10');
        scope.endDate = moment('2014-07-11');

        chart = $compile(chart)(scope);
        scope.$digest();

        isolate = chart.isolateScope();

        isolate.data = data;
        isolate.$digest();
    }));

    it('should set xAxis range properly', function () {
        expect(isolate.config.options.xAxis.min).toBe(moment.utc('2014-07-10').valueOf());
        expect(isolate.config.options.xAxis.max).toBe(moment.utc('2014-07-11').valueOf());
    });

    it('should set totals series correctly', function () {
        var totalsSeries = isolate.config.series[0];

        expect(totalsSeries.name).toBe('Totals (Spend)');
        expect(totalsSeries.color).toBe('#009db2');
        expect(totalsSeries.yAxis).toBe(0);
        expect(totalsSeries.tooltip.pointFormat).toBe('Totals (Spend): <b>${point.y:,.2f}</b></br>');

        expect(totalsSeries.marker.radius).toBe(3);
        expect(totalsSeries.marker.symbol).toBe('square');
        expect(totalsSeries.marker.fillColor).toBe('#009db2');
        expect(totalsSeries.marker.lineWidth).toBe(2);
        expect(totalsSeries.marker.lineColor).toBe(null);

        expect(totalsSeries.data).toEqual([
            [1404950400000, 205.1312],
            [1405036800000, 128.5189]
        ]);
    });
});
