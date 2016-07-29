/* globals angular, constants, moment, jasmine, describe, it, beforeEach, expect, module, inject, spyOn */

describe('zemGridEndpointServiceSpec', function () {
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

    it('should configure columns', function () {
        var columns = zemGridEndpointColumns.createColumns($scope, constants.level.CAMPAIGNS, [constants.breakdown.AD_GROUP, constants.breakdown.CONTENT_AD, constants.breakdown.MEDIA_SOURCE]);
        var nameColumn = findColumn(zemGridEndpointColumns.COLUMNS.name, columns);
        expect (nameColumn.permanent).toBe(true);
        expect (nameColumn.default).toBe(true);
        expect (nameColumn.breakdowns).toBeFalsy();
        expect (nameColumn.goal).toBeFalsy();

        var cpcColumn = findColumn(zemGridEndpointColumns.COLUMNS.cpc, columns);
        expect (cpcColumn.permanent).toBeFalsy();
        expect (cpcColumn.default).toBe(true);
        expect (cpcColumn.breakdowns).toBeFalsy();
        expect (cpcColumn.goal).toBeFalsy();

        var minBidCpcColumn = findColumn(zemGridEndpointColumns.COLUMNS.minBidCpc, columns);
        expect (minBidCpcColumn.permanent).toBeFalsy();
        expect (minBidCpcColumn.default).toBeFalsy();
        expect (minBidCpcColumn.breakdowns).toEqual(['source']);
        expect (minBidCpcColumn.goal).toBeFalsy();

        var avgCostPerMinuteColumn = findColumn(zemGridEndpointColumns.COLUMNS.avgCostPerMinute, columns);
        expect (avgCostPerMinuteColumn.permanent).toBeFalsy();
        expect (avgCostPerMinuteColumn.default).toBeFalsy();
        expect (avgCostPerMinuteColumn.breakdowns).toBeFalsy();
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

});
