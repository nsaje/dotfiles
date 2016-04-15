'use strict';

describe('AdGroupCtrl', function () {
    var $scope, parentScope, $state, user;

    beforeEach(function () {
        module('one');

        inject(function ($rootScope, $controller, _$state_, zemLocalStorageService) {
            parentScope = $rootScope.$new();
            $scope = parentScope.$new();

            $scope.adGroupData = {};

            $state = _$state_;
            $state.params.id = 1;

            user = {
                permissions: {}
            };

            zemLocalStorageService.init(user);
            $controller('MainCtrl', {
                $scope: parentScope,
                $state: $state,
                user: user,
                accountsAccess: {
                    hasAccounts: true,
                },
                zemFullStoryService: {identify: function () {}}
            });
            $controller('AdGroupCtrl', {
                $scope: $scope,
                $state: $state,
                adGroupData: {
                    account: {
                        id: 4,
                    },
                    campaign: {
                        id: 2,
                    },
                    adGroup: {
                        id: 3,
                    },
                },
            });
        });
    });

    it('inits models propery', function () {
        expect($scope.adGroup.id, 3);
        expect($scope.campaign.id, 2);
        expect($scope.account.id, 4);
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
