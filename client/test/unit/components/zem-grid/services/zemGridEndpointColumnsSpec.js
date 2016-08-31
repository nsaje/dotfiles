/* globals angular, constants, moment, jasmine, describe, it, beforeEach, expect, module, inject, spyOn */

describe('zemGridEndpointColumnsSpec', function () {
    var $scope;
    var zemGridEndpointColumns;

    beforeEach(module('one'));

    beforeEach(inject(function ($rootScope, _zemGridEndpointColumns_) { // eslint-disable-line max-len
        zemGridEndpointColumns = _zemGridEndpointColumns_;

        $scope = $rootScope.$new();
        $scope.isPermissionInternal = function () {
            return false;
        };
        $scope.hasPermission = function () {
            return true;
        };
    }));

    function findColumn (originalColumn, columns) {
        return columns.filter(function (column) {
            return column.field === originalColumn.field;
        })[0];
    }

    function findColumnByField (field, columns) {
        return findColumn({field: field}, columns);
    }

    it('should configure columns', function () {
        var columns = zemGridEndpointColumns.createColumns($scope, constants.level.CAMPAIGNS, [constants.breakdown.AD_GROUP, constants.breakdown.CONTENT_AD, constants.breakdown.MEDIA_SOURCE]);
        var nameColumn = findColumn(zemGridEndpointColumns.COLUMNS.name, columns);
        expect (nameColumn.permanent).toBe(true);
        expect (nameColumn.default).toBe(true);
        expect (nameColumn.exceptions.breakdowns).toBeFalsy();
        expect (nameColumn.goal).toBeFalsy();

        var cpcColumn = findColumn(zemGridEndpointColumns.COLUMNS.cpc, columns);
        expect (cpcColumn.permanent).toBeFalsy();
        expect (cpcColumn.default).toBe(true);
        expect (cpcColumn.exceptions.breakdowns).toBeFalsy();
        expect (cpcColumn.goal).toBeFalsy();

        var minBidCpcColumn = findColumn(zemGridEndpointColumns.COLUMNS.minBidCpc, columns);
        expect (minBidCpcColumn.permanent).toBeFalsy();
        expect (minBidCpcColumn.default).toBeFalsy();
        expect (minBidCpcColumn.exceptions.breakdowns).toEqual(['source']);
        expect (minBidCpcColumn.goal).toBeFalsy();

        var avgCostPerMinuteColumn = findColumn(zemGridEndpointColumns.COLUMNS.avgCostPerMinute, columns);
        expect (avgCostPerMinuteColumn.permanent).toBeFalsy();
        expect (avgCostPerMinuteColumn.default).toBeFalsy();
        expect (avgCostPerMinuteColumn.exceptions.breakdowns).toBeFalsy();
        expect (avgCostPerMinuteColumn.goal).toBe(true);
    });

    it('should brand permanent columns', function () {
        var columns = zemGridEndpointColumns.createColumns($scope, constants.level.CAMPAIGNS,
            [constants.breakdown.AD_GROUP, constants.breakdown.CONTENT_AD, constants.breakdown.MEDIA_SOURCE]);

        var nameColumn = findColumn(zemGridEndpointColumns.COLUMNS.name, columns);
        expect(nameColumn.name).toBe ('Ad Group');
        expect(nameColumn.help).toBe ('Name of the ad group.');

        var statusColumn = findColumn(zemGridEndpointColumns.COLUMNS.status, columns);
        expect(statusColumn.name).toBe ('Status');
        expect(statusColumn.help.indexOf('Status of an ad group')).toBe (0);

        var stateColumn = findColumn(zemGridEndpointColumns.COLUMNS.state, columns);
        expect(stateColumn.name).toBe ('\u25CF');
        expect(stateColumn.help).toBe ('A setting for enabling and pausing Ad Groups.');

    });

    it('should create columns based on breakdown', function () {
        var columns = zemGridEndpointColumns.createColumns($scope, constants.level.ALL_ACCOUNTS,
            [constants.breakdown.ACCOUNT, constants.breakdown.CAMPAIGN, constants.breakdown.MEDIA_SOURCE]);

        var stateColumn = findColumn(zemGridEndpointColumns.COLUMNS.state, columns);
        expect(stateColumn).toBe(undefined);

        var minBidCpcColumn = findColumn(zemGridEndpointColumns.COLUMNS.minBidCpc, columns);
        expect(minBidCpcColumn).toEqual(jasmine.any(Object));

        var imageUrlsColumn = findColumn(zemGridEndpointColumns.COLUMNS.imageUrls, columns);
        expect(imageUrlsColumn).toBe(undefined);
    });

    it('should set dynamic columns correctly', function () {
        var columns = zemGridEndpointColumns.createColumns($scope, constants.level.CAMPAIGNS, [constants.breakdown.AD_GROUP]);
        var categories = zemGridEndpointColumns.createCategories();

        var pixels = [{prefix: 'pixel_1', name: 'Pixel goal'}];
        var conversionGoals = [{id: 'conversion_goal_1', name: 'Conversion goal'}];
        var campaignGoals = [
            {fields: {avg_cost_per_pixel_1_24: true}, name: 'Avg. CPA', conversion: 'Pixel goal - 1 day', value: 20, primary: true},
            {fields: {avg_cost_per_conversion_goal_1: true}, name: 'Avg. CPA', conversion: 'Conversion goal', value: 50, primary: false},
        ];

        zemGridEndpointColumns.setDynamicColumns(columns, categories, campaignGoals, conversionGoals, pixels);

        var pixelConversionsColumn = findColumnByField('pixel_1_24', columns);
        expect(pixelConversionsColumn.shortName).toBe(1);
        expect(pixelConversionsColumn.permanent).toBeFalsy();
        expect(pixelConversionsColumn.default).toBeFalsy();
        expect(pixelConversionsColumn.goal).toBeFalsy();

        var pixelCpaColumn = findColumnByField('avg_cost_per_pixel_1_24', columns);
        expect(pixelCpaColumn.permanent).toBeFalsy();
        expect(pixelCpaColumn.default).toBe(true);
        expect(pixelCpaColumn.goal).toBe(true);
        expect(pixelCpaColumn.autoSelect).toBe('pixel_1_24');

        var goalConversionsColumn = findColumnByField('conversion_goal_1', columns);
        expect(goalConversionsColumn.permanent).toBeFalsy();
        expect(goalConversionsColumn.default).toBeFalsy();
        expect(goalConversionsColumn.goal).toBeFalsy();

        var goalCpaColumn = findColumnByField('avg_cost_per_conversion_goal_1', columns);
        expect(goalCpaColumn.permanent).toBeFalsy();
        expect(goalCpaColumn.default).toBeFalsy();
        expect(goalCpaColumn.goal).toBe(true);
    });

});
