'use strict';

describe('AdGroupAdsPlusCtrl', function() {
    var $scope, api, $q, $timeout, $state;
    var zemFilterServiceMock;

    beforeEach(module('one'));
    beforeEach(module(function ($provide) {
        zemFilterServiceMock = {
            getShowArchived: function() {}
        };

        $provide.value('zemLocalStorageService', {get: function(){}});
        $provide.value('zemFilterService', zemFilterServiceMock);
        $provide.value('zemCustomTableColsService', {
            load: function() {return [];},
            save: function() {return [];}
        });
    }));

    beforeEach(inject(function($controller, $rootScope, _$q_, _$timeout_, _$state_) {
        $q = _$q_;
        $timeout = _$timeout_;
        $scope = $rootScope.$new();

        $scope.isPermissionInternal = function() {return true;};
        $scope.hasPermission = function() {return true;};
        $scope.getAdGroupState = function() {};
        $scope.dateRange = {
            startDate: {
                isSame: function() {}
            }
        };

        $scope.adGroup = {contentAdsTabWithCMS: false};

        var tf = function() {
            return {
                then: function() {
                    return {
                        finally: function() {}
                    };
                }
            };
        };
        api = {
            adGroupContentAdArchive: {
                archive: function() {},
                restore: function() {}
            },
            adGroupAdsPlusTable: {
                get: tf,
                getUpdates: tf
            },
            dailyStats: {
                listContentAdStats: tf
            },
            adGroupAdsPlusUploadBatches: {
                list: tf
            },
            adGroupAdsPlusExportAllowed: {
                get: tf
            }
        };

        $state = _$state_;
        $state.params = {id: 123};

        $controller('AdGroupAdsPlusCtrl', {$scope: $scope, api: api, $state: $state});
    }));

    describe('addContentAds', function(done) {
        it('opens a modal window when called', function() {
            $scope.addContentAds().result
                .catch(function(error) {
                    expect(error).toBeUndefined();
                })
                .finally(done);
        });
    });

    describe('archiveContentAds', function(done) {
        it('calls api to archive all when none selected', function() {
            var deferred = $q.defer();

            spyOn(api.adGroupContentAdArchive, 'archive').and.callFake(function() {
                return deferred.promise;
            });

            $scope.bulkArchiveContentAds([], []);

            expect(api.adGroupContentAdArchive.archive).toHaveBeenCalledWith(
                $state.params.id, [], [], true, null
            );
        });
        it('does nothing on failure', function() {
            var deferred = $q.defer();

            spyOn(api.adGroupContentAdArchive, 'archive').and.callFake(function() {
                return deferred.promise;
            });

            spyOn($scope, 'updateTableAfterArchiving');

            $scope.bulkArchiveContentAds([], []);

            deferred.reject();

            expect($scope.updateTableAfterArchiving).not.toHaveBeenCalled();
        });
        it('does update table on success', function() {
            zemFilterServiceMock.getShowArchived = function() { return false; };

            var data = {data: {rows: []}};
            api.adGroupContentAdArchive.archive = function() {
                return {
                    then: function(handler) {
                        handler(data);
                    }
                };
            };

            spyOn($scope, 'updateTableAfterArchiving');

            $scope.bulkArchiveContentAds([], []);

            expect($scope.updateTableAfterArchiving).toHaveBeenCalledWith(data);
        });
    });

    describe('restoreContentAds', function(done) {
        it('calls api to restore all when none selected', function() {
            var deferred = $q.defer();

            spyOn(api.adGroupContentAdArchive, 'restore').and.callFake(function() {
                return deferred.promise;
            });

            $scope.bulkRestoreContentAds([], []);

            expect(api.adGroupContentAdArchive.restore).toHaveBeenCalledWith(
                $state.params.id, [], [], true, null
            );
        });
        it('does nothing on failure', function() {
            var deferred = $q.defer();

            spyOn(api.adGroupContentAdArchive, 'restore').and.callFake(function() {
                return deferred.promise;
            });

            spyOn($scope, 'updateTableAfterArchiving');

            $scope.bulkRestoreContentAds([], []);

            deferred.reject();

            expect($scope.updateTableAfterArchiving).not.toHaveBeenCalled();
        });
        it('does update table on success', function() {
            var data = {data: {rows: []}};
            api.adGroupContentAdArchive.restore = function() {
                return {
                    then: function(handler) {
                        handler(data);
                    }
                };
            };

            spyOn($scope, 'updateTableAfterArchiving');

            $scope.bulkRestoreContentAds([], []);

            expect($scope.updateTableAfterArchiving).toHaveBeenCalledWith(data);
        });
    });
});
