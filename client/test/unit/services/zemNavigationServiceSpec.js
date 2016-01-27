/* globals describe, beforeEach, module, spyOn, expect, it, inject */
'use strict';

describe('zemNavigationService', function () {

    var zemNavigationService,
        $scope,
        $q,
        apiMock,
        mockApiFunc;

    beforeEach(function () {
        mockApiFunc = function () {
            return {
                then: function () {
                    return {
                        finally: function () {},
                    };
                },
            };
        };
        apiMock = {
            navigation: {
                list: mockApiFunc,
                getAdGroup: mockApiFunc,
                getCampaign: mockApiFunc,
                getAccount: mockApiFunc,
                getAccountsAccess: mockApiFunc,
            },
        };

        module('one');

        module(function ($provide) {
            $provide.value('api', apiMock);
        });

        inject(function ($rootScope, _$q_, _zemNavigationService_) {
            zemNavigationService = _zemNavigationService_;
            $scope = $rootScope.$new();
            $q = _$q_;
        });

        spyOn(apiMock.navigation, 'getAdGroup').and.callFake(mockApiFunc);
        spyOn(apiMock.navigation, 'getCampaign').and.callFake(mockApiFunc);
        spyOn(apiMock.navigation, 'getAccount').and.callFake(mockApiFunc);
        spyOn(apiMock.navigation, 'getAccountsAccess').and.callFake(mockApiFunc);

    });

    describe('Fetch data from server when cache is not available', function () {
        it('initial state of accounts is []', function () {
            expect(zemNavigationService.getAccounts()).toEqual([]);
        });

        it('calls api when getting adGroup', function () {
            zemNavigationService.getAdGroup(2);
            expect(apiMock.navigation.getAdGroup).toHaveBeenCalledWith(2);
        });

        it('calls api when getting campaign', function () {
            zemNavigationService.getCampaign(3);
            expect(apiMock.navigation.getCampaign).toHaveBeenCalledWith(3);
        });

        it('calls api when getting account', function () {
            zemNavigationService.getAccount(4);
            expect(apiMock.navigation.getAccount).toHaveBeenCalledWith(4);
        });

        it('calls api when getting accounts access', function () {
            zemNavigationService.getAccountsAccess();
            expect(apiMock.navigation.getAccountsAccess).toHaveBeenCalled();
        });
    });

    describe('Cache available', function () {
        var adGroup3 = {id: 3, name: 'ad 3'},
            adGroup7 = {id: 7, name: 'ad 7'},
            campaign2 = {id: 2, name: 'ca', adGroups: [adGroup3, adGroup7]},
            account1 = {id: 1, name: 'acc 1', campaigns: [campaign2]},
            account2 = {id: 2, name: 'acc 2', campaigns: []},
            accounts = [account1, account2];

        beforeEach(function () {
            var deferred = $q.defer();
            spyOn(apiMock.navigation, 'list').and.callFake(function () {
                return deferred.promise;
            });
            zemNavigationService.reload();

            deferred.resolve(accounts);
            $scope.$digest();
        });

        describe('Fetch from cache when available', function () {
            it('cache is set after reload', function () {
                expect(zemNavigationService.getAccounts()).toEqual(accounts);
            });

            it('doesn\'t call api when getting adGroup', function () {
                zemNavigationService.getAdGroup(3);
                expect(apiMock.navigation.getAdGroup).not.toHaveBeenCalled();
            });

            it('doesn\'t call api when getting campaign', function () {
                zemNavigationService.getCampaign(2);
                expect(apiMock.navigation.getCampaign).not.toHaveBeenCalled();
            });

            it('doesn\'t call api when getting account', function () {
                zemNavigationService.getAccount(1);
                expect(apiMock.navigation.getAccount).not.toHaveBeenCalled();
            });

            it('doesn\'t call api when getting accounts access', function () {
                zemNavigationService.getAccountsAccess();
                expect(apiMock.navigation.getAccountsAccess).not.toHaveBeenCalled();
            });
        });

        describe('Notifies subscribers when cache is updated', function () {
            it('notifies onUpdate subscribers when cache is updated', function () {
                $scope.controllerMock = {
                    update: function () {},
                };

                spyOn($scope.controllerMock, 'update');
                zemNavigationService.onUpdate($scope, $scope.controllerMock.update);

                zemNavigationService.updateAdGroupCache(3, {
                    name: 'ad updated',
                });

                expect($scope.controllerMock.update).toHaveBeenCalled();
            });

            it('notifies onLoading subscribers when navigation is being fetched', function () {
                var controllerMock = {
                    loading: function () {},
                };

                spyOn(controllerMock, 'loading');
                zemNavigationService.onLoading($scope, controllerMock.loading);

                zemNavigationService.reload();

                expect(controllerMock.loading).toHaveBeenCalled();
            });
        });

        describe('Cache is being queried correctly', function () {
            it('retrieves the correct ad group', function () {
                zemNavigationService.getAdGroup(7).then(function (data) {
                    expect(data).toEqual({
                        adGroup: adGroup7,
                        campaign: campaign2,
                        account: account1,
                    });
                });
                $scope.$digest();
            });

            it('retrieves the correct campaign', function () {
                zemNavigationService.getCampaign(2).then(function (data) {
                    expect(data).toEqual({
                        campaign: campaign2,
                        account: account1,
                    });
                });
                $scope.$digest();
            });

            it('retrieves the correct account', function () {
                zemNavigationService.getAccount(1).then(function (data) {
                    expect(data).toEqual({
                        account: account1,
                    });
                });
                $scope.$digest();
            });

            it('retrieves the correct accounts access', function () {
                zemNavigationService.getAccountsAccess(1).then(function (data) {
                    expect(data).toEqual({
                        hasAccounts: true,
                    });
                });

                $scope.$digest();
            });
        });

        describe('Cache is being updated correctly', function () {
            it('updates ad group correctly', function () {
                zemNavigationService.updateAdGroupCache(3, {
                    name: 'Changed name',
                });

                zemNavigationService.getAdGroup(3).then(function (data) {
                    expect(data.adGroup.name).toEqual('Changed name');
                });
                $scope.$digest();
            });

            it('updates campaign correctly', function () {
                zemNavigationService.updateCampaignCache(2, {
                    name: 'Changed name',
                });

                zemNavigationService.getCampaign(2).then(function (data) {
                    expect(data.campaign.name).toEqual('Changed name');
                });
                $scope.$digest();
            });

            it('updates account correctly', function () {
                zemNavigationService.updateAccountCache(1, {
                    name: 'Changed name',
                });

                zemNavigationService.getAccount(1).then(function (data) {
                    expect(data.account.name).toEqual('Changed name');
                });
                $scope.$digest();
            });

            it('adds ad group successfully', function () {
                var adGroup = {id: 9, name: 'ad 9'};
                zemNavigationService.addAdGroupToCache(2, adGroup);
                zemNavigationService.getCampaign(2).then(function (data) {
                    expect(data.campaign.adGroups[2]).toBe(adGroup);
                });
                $scope.$digest();
            });

            it('adds campaign successfully', function () {
                var campaign = {id: 9, name: 'ca 9'};
                zemNavigationService.addCampaignToCache(1, campaign);
                zemNavigationService.getAccount(1).then(function (data) {
                    expect(data.account.campaigns[1]).toBe(campaign);
                });
                $scope.$digest();
            });

            it('adds account successfully', function () {
                var account = {id: 9, name: 'acc 9'};
                zemNavigationService.addAccountToCache(account);
                expect(zemNavigationService.getAccounts()[2]).toBe(account);
            });
        });
    });
});
