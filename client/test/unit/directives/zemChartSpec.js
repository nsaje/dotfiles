'use strict';

describe('zemChartLegacy', function () {
    var scope, chart, isolate;
    var data = {
        id: 'totals',
        groups: [{
            id: 'totals',
            name: 'Totals',
            seriesData: {
                media_cost: [
                    ['2014-07-10', 205.1312],
                    ['2014-07-11', 128.5189],
                ],
            },
        }]
    };

    beforeEach(module('one'));

    beforeEach(inject(function ($rootScope, $compile) {
        scope = $rootScope.$new();

        chart = '<zem-chart-legacy zem-data="chartData" zem-metric1="chartMetric1" zem-metric2="chartMetric2" zem-metric-options="chartMetricOptions" zem-min-date="startDate" zem-max-date="endDate"></zem-chart-legacy>';

        scope.chartMetric1 = 'media_cost';
        scope.chartMetricOptions = [{name: 'Media Spend', value: 'media_cost'}];
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

        expect(totalsSeries.name).toBe('Totals (Media Spend)');
        expect(totalsSeries.color).toBe('#3f547f');
        expect(totalsSeries.yAxis).toBe(0);
        expect(totalsSeries.tooltip.pointFormat).toBe('<div class="color-box" style="background-color: #3f547f"></div>Totals (Media Spend): <b>${point.y:,.2f}</b></br>');

        expect(totalsSeries.marker.radius).toBe(3);
        expect(totalsSeries.marker.symbol).toBe('square');
        expect(totalsSeries.marker.fillColor).toBe('#3f547f');
        expect(totalsSeries.marker.lineWidth).toBe(2);
        expect(totalsSeries.marker.lineColor).toBe(null);

        expect(totalsSeries.data).toEqual([
            [1404950400000, 205.1312],
            [1405036800000, 128.5189]
        ]);
    });

    it('should add a null datapoint on the first date without data', function () {
        scope.startDate = moment('2014-07-01');
        scope.endDate = moment('2014-07-30');
        isolate.data = {
            groups: [{
                id: 'totals',
                name: 'Totals',
                seriesData: {
                    media_cost: [
                        ['2014-07-10', 205.1312],
                        ['2014-07-11', 128.5189],
                        ['2014-07-15', 138.5189],
                        ['2014-07-17', 148.5189],
                        ['2014-07-18', 158.5189]
                    ]
                }
            }]
        };

        scope.$digest();
        isolate.$digest();

        var totalsSeries = isolate.config.series[0], msInADay = 24 * 3600 * 1000;
        expect(totalsSeries.data).toEqual([
            [1404950400000, 205.1312],
            [1405036800000, 128.5189],
            [1405123200000, null],
            [1405382400000, 138.5189],
            [1405468800000, null],
            [1405555200000, 148.5189],
            [1405641600000, 158.5189]
        ]);
    });
});
