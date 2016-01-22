'use strict';

describe('AdGroupCtrl', function () {
    var $scope, parentScope, $state, user, accounts;

    beforeEach(function () {
        module('one');

        inject(function ($rootScope, $controller, _$state_, zemLocalStorageService) {
            parentScope = $rootScope.$new();
            $scope = parentScope.$new();

            $scope.adGroupData = {};
            $scope.accounts = [{
                id: 1,
                campaigns: [{
                    id: 1,
                    adGroups: [{
                        id: 1
                    }]
                }]
            }];

            $state = _$state_;
            $state.params.id = 1;

            user = {
                permissions: {}
            };

            accounts = [];

            zemLocalStorageService.init(user);
            $controller('MainCtrl', {
                $scope: parentScope,
                $state: $state,
                user: user,
                accounts: accounts,
                zemFullStoryService: {identify: function () {}}
            });
            $controller('AdGroupCtrl', {$scope: $scope, $state: $state});
        });
    });

    it('shows Content Ads+ tab when ad group has cms turned on', function () {
        $scope.adGroup.contentAdsTabWithCMS = true;
        var tabs = $scope.getTabs();
        expect(tabs[0].route, 'main.adGroups.adsPlus');
    });

    it('hides Content Ads+ tab when no permission', function () {
        var tabs = $scope.getTabs();
        expect(tabs.length).toEqual(5);
    });

    it('sets hidden and internal for Content Ads+ tab', function () {
        $scope.user.permissions['zemauth.new_content_ads_tab'] = false;

        var tabs = $scope.getTabs();

        expect(tabs[5].hidden).toEqual(false);
        expect(tabs[5].internal).toEqual(true);
    });

    describe('setAdGroupData', function () {
        it('should add key-value pair for the current ad group', function () {
            $scope.adGroupData = {1: {key1: 'value1'}};
            $scope.setAdGroupData('key2', 'value2');
            expect($scope.adGroupData).toEqual({
                1: {
                    key1: 'value1',
                    key2: 'value2'
                }
            });
        });

        it('should store key-value pair for the current ad group even when nothing has been stored yet', function () {
            $scope.adGroupData = {};
            $scope.setAdGroupData('key2', 'value2');
            expect($scope.adGroupData).toEqual({
                1: {
                    key2: 'value2'
                }
            });
        });
    });
});
