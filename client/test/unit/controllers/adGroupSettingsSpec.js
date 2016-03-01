'use strict';

describe('AdGroupSettingsCtrlSpec', function () {
    var api, $scope;

    beforeEach(module('one'));

    beforeEach(inject(function ($rootScope, $controller, _$timeout_, $state) {
        $scope = $rootScope.$new();
        $scope.adGroup = {archived: false};
        $scope.account = {id: 1};

        var mockApiFunc = function () {
            return {
                then: function () {
                    return {
                        finally: function () {},
                    };
                },
            };
        };

        api = {
            adGroupSettings: {
                get: mockApiFunc
            },
        };

        $controller('AdGroupSettingsCtrl', {$scope: $scope, api: api});
    }));

    describe('isDefaultTargetRegions', function () {
        beforeEach(function () {
            $scope.settings = {targetRegions: []};
            $scope.defaultSettings = {targetRegions: []};
        });

        it('return true if targetRegions are equal to default targetRegions', function () {
            $scope.settings.targetRegions = ['US', '501'];
            $scope.defaultSettings.targetRegions = ['US', '501'];

            expect($scope.isDefaultTargetRegions()).toBe(true);
        });

        it('return true if targetRegions are equal to default targetRegions', function () {
            $scope.settings.targetRegions = ['US', '501'];
            $scope.defaultSettings.targetRegions = ['US', '501', '502'];

            expect($scope.isDefaultTargetRegions()).toBe(false);
        });
    });

    describe('isDefaultTargetDevices', function () {
        beforeEach(function () {
            $scope.settings = {targetDevices: []};
            $scope.defaultSettings = {targetDevices: []};
        });

        it('return true if targetDevices are equal to default targetDevices', function () {
            $scope.settings.targetDevices = [
                {value: 'mobile', checked: true},
                {value: 'desktop', checked: false}
            ];
            $scope.defaultSettings.targetDevices = [
                {value: 'mobile', checked: true},
                {value: 'desktop', checked: false}
            ];

            expect($scope.isDefaultTargetDevices()).toBe(true);
        });

        it('return true if targetDevices are equal to default targetDevices', function () {
            $scope.settings.targetDevices = [
                {value: 'mobile', checked: true},
                {value: 'desktop', checked: false}
            ];
            $scope.defaultSettings.targetDevices = [
                {value: 'mobile', checked: true},
                {value: 'desktop', checked: true}
            ];

            expect($scope.isDefaultTargetDevices()).toBe(false);
        });
    });
});
