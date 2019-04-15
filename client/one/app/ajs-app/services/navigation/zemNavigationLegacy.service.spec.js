describe('zemNavigationService', function() {
    var zemNavigationService,
        zemNavigationLegacyEndpoint,
        $scope,
        $q,
        mockApiFunc;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(function() {
        mockApiFunc = function() {
            return {
                then: function() {
                    return {
                        finally: function() {},
                    };
                },
            };
        };

        inject(function(
            $rootScope,
            _$q_,
            _zemNavigationService_,
            _zemNavigationLegacyEndpoint_
        ) {
            zemNavigationLegacyEndpoint = _zemNavigationLegacyEndpoint_;
            zemNavigationService = _zemNavigationService_;
            $scope = $rootScope.$new();
            $q = _$q_;
        });

        spyOn(zemNavigationLegacyEndpoint, 'getAdGroup').and.callFake(
            mockApiFunc
        );
        spyOn(zemNavigationLegacyEndpoint, 'getCampaign').and.callFake(
            mockApiFunc
        );
        spyOn(zemNavigationLegacyEndpoint, 'getAccount').and.callFake(
            mockApiFunc
        );
        spyOn(zemNavigationLegacyEndpoint, 'getAccountsAccess').and.callFake(
            mockApiFunc
        );
    });

    describe('Fetch data from server when cache is not available', function() {
        it('initial state of accounts is []', function() {
            expect(zemNavigationService.getAccounts()).toEqual([]);
        });

        it('calls api when getting adGroup', function() {
            zemNavigationService.getAdGroup(2);
            expect(zemNavigationLegacyEndpoint.getAdGroup).toHaveBeenCalledWith(
                2
            );
        });

        it('calls api when getting campaign', function() {
            zemNavigationService.getCampaign(3);
            expect(
                zemNavigationLegacyEndpoint.getCampaign
            ).toHaveBeenCalledWith(3);
        });

        it('calls api when getting account', function() {
            zemNavigationService.getAccount(4);
            expect(zemNavigationLegacyEndpoint.getAccount).toHaveBeenCalledWith(
                4
            );
        });

        it('calls api when getting accounts access', function() {
            zemNavigationService.getAccountsAccess();
            expect(
                zemNavigationLegacyEndpoint.getAccountsAccess
            ).toHaveBeenCalled();
        });
    });

    describe('Cache available', function() {
        var adGroup3 = {id: 3, name: 'ad 3'},
            adGroup7 = {id: 7, name: 'ad 7'},
            campaign2 = {id: 2, name: 'ca', adGroups: [adGroup3, adGroup7]},
            account1 = {id: 1, name: 'acc 1', campaigns: [campaign2]},
            account2 = {id: 2, name: 'acc 2', campaigns: []},
            accounts = [account1, account2];

        beforeEach(function() {
            var deferred = $q.defer();
            spyOn(zemNavigationLegacyEndpoint, 'list').and.callFake(function() {
                return deferred.promise;
            });
            zemNavigationService.reload();

            deferred.resolve(accounts);
            $scope.$digest();
        });

        describe('Fetch from cache when available', function() {
            it('cache is set after reload', function() {
                expect(zemNavigationService.getAccounts()).toEqual(accounts);
            });

            it("doesn't call api when getting adGroup", function() {
                zemNavigationService.getAdGroup(3);
                expect(
                    zemNavigationLegacyEndpoint.getAdGroup
                ).not.toHaveBeenCalled();
            });

            it("doesn't call api when getting campaign", function() {
                zemNavigationService.getCampaign(2);
                expect(
                    zemNavigationLegacyEndpoint.getCampaign
                ).not.toHaveBeenCalled();
            });

            it("doesn't call api when getting account", function() {
                zemNavigationService.getAccount(1);
                expect(
                    zemNavigationLegacyEndpoint.getAccount
                ).not.toHaveBeenCalled();
            });
        });

        describe('Notifies subscribers when cache is updated', function() {
            it('notifies onUpdate subscribers when cache is updated', function() {
                $scope.controllerMock = {
                    update: function() {},
                };

                spyOn($scope.controllerMock, 'update');
                zemNavigationService.onUpdate(
                    $scope,
                    $scope.controllerMock.update
                );
                zemNavigationLegacyEndpoint.getAccount.and.callFake(function() {
                    return $q.resolve({account: account1});
                });

                zemNavigationService.reloadAccount(1).then(function() {
                    expect($scope.controllerMock.update).toHaveBeenCalled();
                });
                $scope.$digest();
            });

            it('notifies onLoading subscribers when navigation is being fetched', function() {
                var controllerMock = {
                    loading: function() {},
                };

                spyOn(controllerMock, 'loading');
                zemNavigationService.onLoading($scope, controllerMock.loading);

                zemNavigationService.reload();

                expect(controllerMock.loading).toHaveBeenCalled();
            });
        });

        describe('Cache is being queried correctly', function() {
            it('retrieves the correct ad group', function() {
                zemNavigationService.getAdGroup(7).then(function(data) {
                    expect(data).toEqual({
                        adGroup: adGroup7,
                        campaign: campaign2,
                        account: account1,
                    });
                });
                $scope.$digest();
            });

            it('retrieves the correct campaign', function() {
                zemNavigationService.getCampaign(2).then(function(data) {
                    expect(data).toEqual({
                        campaign: campaign2,
                        account: account1,
                    });
                });
                $scope.$digest();
            });

            it('retrieves the correct account', function() {
                zemNavigationService.getAccount(1).then(function(data) {
                    expect(data).toEqual({
                        account: account1,
                    });
                });
                $scope.$digest();
            });

            it('retrieves the correct accounts access', function() {
                zemNavigationService.getAccountsAccess(1).then(function(data) {
                    expect(data).toEqual({
                        hasAccounts: true,
                    });
                });

                $scope.$digest();
            });
        });
    });
});
