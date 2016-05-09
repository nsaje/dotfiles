'use strict';

describe('zemPostclickMetricsServiceSpec', function () {
    var postclickMetricsService = null;

    beforeEach(module('one'));
    beforeEach(inject(function (_zemPostclickMetricsService_) {
        postclickMetricsService = _zemPostclickMetricsService_;
    }));

    describe('setConversionGoalChartOptions function', function () {
        it('should not change conversion goal chart metrics when there are no conversion goals', function () {
            var options = [{
                value: 'conversion_goal_1',
                name: 'Default name 1',
                shown: false
            }, {
                value: 'conversion_goal_2',
                name: 'Default name 2',
                shown: false
            }];

            postclickMetricsService.setConversionGoalChartOptions(options, []);

            expect(options).toEqual([{
                value: 'conversion_goal_1',
                name: 'Default name 1',
                shown: false
            }, {
                value: 'conversion_goal_2',
                name: 'Default name 2',
                shown: false
            }]);
        });

        it('should change names', function () {
            var options = [{
                value: 'conversion_goal_1',
                name: 'Default name 1',
                shown: false
            }, {
                value: 'conversion_goal_2',
                name: 'Default name 2',
                shown: false
            }];
            var conversionGoals = [{id: 'conversion_goal_1', 'name': 'Goal name 1'}];

            postclickMetricsService.setConversionGoalChartOptions(options, conversionGoals);

            expect(options).toEqual([{
                value: 'conversion_goal_1',
                name: 'Goal name 1',
                shown: true
            }, {
                value: 'conversion_goal_2',
                name: 'Default name 2',
                shown: false 
            }]);
        });

        it('should change shown property correctly', function () {
            var options = [{
                value: 'conversion_goal_1',
                name: 'Default name 1',
                shown: false
            }, {
                value: 'conversion_goal_2',
                name: 'Default name 2',
                shown: false
            }];
            var conversionGoals = [{id: 'conversion_goal_1', 'name': 'Goal name 1'}];

            postclickMetricsService.setConversionGoalChartOptions(options, conversionGoals);

            expect(options).toEqual([{
                value: 'conversion_goal_1',
                name: 'Goal name 1',
                shown: true
            }, {
                value: 'conversion_goal_2',
                name: 'Default name 2',
                shown: false
            }]);
        });
    });

    describe('setConversionGoalColumnsDefaults function', function () {
        it('should not change conversion goal columns when there are no conversion goals', function () {
            var cols = [{
                field: 'conversion_goal_1',
                name: 'Default name 1',
                shown: false
            }, {
                field: 'conversion_goal_2',
                name: 'Default name 2',
                shown: false
            }];

            postclickMetricsService.setConversionGoalColumnsDefaults(cols, [], true);

            expect(cols).toEqual([{
                field: 'conversion_goal_1',
                name: 'Default name 1',
                shown: false
            }, {
                field: 'conversion_goal_2',
                name: 'Default name 2',
                shown: false
            }]);
        });

        it('should change conversion goal names', function () {
            var cols = [{
                field: 'conversion_goal_1',
                name: 'Default name 1',
                shown: false
            }, {
                field: 'conversion_goal_2',
                name: 'Default name 2',
                shown: false
            }];

            var conversionGoals = [{id: 'conversion_goal_1', 'name': 'Goal name 1'}];

            postclickMetricsService.setConversionGoalColumnsDefaults(cols, conversionGoals, true);

            expect(cols).toEqual([{
                field: 'conversion_goal_1',
                name: 'Goal name 1',
                shown: true
            }, {
                field: 'conversion_goal_2',
                name: 'Default name 2',
                shown: false
            }]);
        });

        it('should change set shown property correctly', function () {
            var cols = [{
                field: 'conversion_goal_1',
                name: 'Default name 1',
                shown: false
            }, {
                field: 'conversion_goal_2',
                name: 'Default name 2',
                shown: false
            }];

            var conversionGoals = [{id: 'conversion_goal_1', 'name': 'Goal name 1'}, {id: 'conversion_goal_2', name: 'Goal name 2'}];

            postclickMetricsService.setConversionGoalColumnsDefaults(cols, conversionGoals, false);

            expect(cols).toEqual([{
                field: 'conversion_goal_1',
                name: 'Goal name 1',
                shown: false
            }, {
                field: 'conversion_goal_2',
                name: 'Goal name 2',
                shown: false
            }]);
        });
    });
});
