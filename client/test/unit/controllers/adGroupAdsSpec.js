/* global constants, describe, spyOn, expect, inject, beforeEach, module, it */
/* eslint-disable camelcase */
'use strict';

describe('AdGroupAdsCtrl', function () {
    var $scope, api, $q, $state, $window;
    var permissions;
    var zemFilterServiceMock;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(module(function ($provide, zemGridDebugEndpointProvider) {
        zemFilterServiceMock = {
            getShowArchived: function () {
                return true;
            },
            getFilteredSources: function () {},
        };

        $provide.value('zemLocalStorageService', {get: function () {}});
        $provide.value('zemFilterService', zemFilterServiceMock);
        $provide.value('zemCustomTableColsService', {
            load: function () {
                return [];
            },
            save: function () {
                return [];
            },
        });
    }));

    beforeEach(inject(function ($controller, $rootScope, _$state_, _$window_, _$q_) {
        $q = _$q_;
        $scope = $rootScope.$new();
        $state = _$state_;
        permissions = {};

        $scope.isPermissionInternal = function () {
            return true;
        };

        $scope.hasPermission = function (permission) {
            if (!permissions.hasOwnProperty(permission)) return true;
            return permissions[permission];
        };
        $scope.dateRange = {
            startDate: {
                isSame: function () {},
            },
            endDate: {
                isSame: function () {},
            },
        };

        $scope.adGroup = {};

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
            adGroupContentAdArchive: {
                archive: mockApiFunc,
                restore: mockApiFunc,
            },
            adGroupAdsTable: {
                get: mockApiFunc,
                getUpdates: mockApiFunc,
            },
            dailyStats: {
                listContentAdStats: mockApiFunc,
            },
            adGroupAdsUploadBatches: {
                list: mockApiFunc,
            },
            adGroupAdsExportAllowed: {
                get: mockApiFunc,
            },
            adGroupContentAdState: {
                save: mockApiFunc,
            },
            exportAllowed: {
                get: mockApiFunc,
            },
            adGroupOverview: {
                get: mockApiFunc,
            },
            campaignOverview: {
                get: mockApiFunc,
            },
        };

        $window = _$window_;
    }));

    function initializeController () {
        inject(function ($controller, $state) {
            $state.params = {id: 1};
            $controller('AdGroupAdsCtrl', {
                $scope: $scope,
                $state: $state,
                api: api,
            });
        });
    }

    describe('archiveContentAds', function () {
        beforeEach(function () {
            initializeController();
            $scope.selectedAll = true;
        });
        it('does nothing on failure', function () {
            var deferred = $q.defer();

            spyOn(api.adGroupContentAdArchive, 'archive').and.callFake(function () {
                return deferred.promise;
            });

            spyOn($scope, 'updateTableAfterArchiving');

            $scope.executeBulkAction('archive');

            deferred.reject();
            $scope.$digest();

            expect(api.adGroupContentAdArchive.archive).toHaveBeenCalled();
            expect($scope.updateTableAfterArchiving).not.toHaveBeenCalled();
        });
        it('updates table on success', function () {
            var deferred = $q.defer();

            spyOn(api.adGroupContentAdArchive, 'archive').and.callFake(function () {
                return deferred.promise;
            });

            spyOn($scope, 'updateTableAfterArchiving');

            $scope.executeBulkAction('archive');

            deferred.resolve({data: {}});
            $scope.$digest();

            expect(api.adGroupContentAdArchive.archive).toHaveBeenCalled();
            expect($scope.updateTableAfterArchiving).toHaveBeenCalled();
        });
    });

    describe('restoreContentAds', function () {
        beforeEach(function () {
            initializeController();
            $scope.selectedAll = true;
        });

        it('does nothing on failure', function () {
            var deferred = $q.defer();

            spyOn(api.adGroupContentAdArchive, 'restore').and.callFake(function () {
                return deferred.promise;
            });

            spyOn($scope, 'updateTableAfterArchiving');

            $scope.executeBulkAction('restore');

            deferred.reject();
            $scope.$digest();

            expect(api.adGroupContentAdArchive.restore).toHaveBeenCalled();
            expect($scope.updateTableAfterArchiving).not.toHaveBeenCalled();
        });
        it('updates table on success', function () {
            var deferred = $q.defer();

            spyOn(api.adGroupContentAdArchive, 'restore').and.callFake(function () {
                return deferred.promise;
            });

            spyOn($scope, 'updateTableAfterArchiving');

            $scope.executeBulkAction('restore');

            deferred.resolve({data: {}});
            $scope.$digest();

            expect(api.adGroupContentAdArchive.restore).toHaveBeenCalled();
            expect($scope.updateTableAfterArchiving).toHaveBeenCalled();
        });
    });

    describe('selectedAdsChanged', function () {
        beforeEach(function () {
            initializeController();
        });
        it('sets correct partialSelection to true if necessary', function () {
            $scope.selectedAdsChanged({id: 1}, true);

            expect($scope.selectionMenuConfig.partialSelection).toBe(true);
        });

        it('sets correct partialSelection to false if necessary', function () {
            $scope.selectedContentAdsStatus = {1: true, 2: true};

            $scope.selectedAdsChanged({id: 1}, false);
            expect($scope.selectionMenuConfig.partialSelection).toBe(true);

            $scope.selectedAdsChanged({id: 2}, false);
            expect($scope.selectionMenuConfig.partialSelection).toBe(false);
        });
        it('acknowledges selection changed when something is selected', function () {
            $scope.selectedContentAdsStatus = {1: true, 2: false};
            $scope.selectedAll = false;
            $scope.selectedBatchId = false;

            expect($scope.isAnythingSelected()).toBe(true);

            $scope.selectedContentAdsStatus[1] = false;

            expect($scope.isAnythingSelected()).toBe(false);

            $scope.selectedAll = true;

            expect($scope.isAnythingSelected()).toBe(true);

            $scope.selectedBatchId = true;

            expect($scope.isAnythingSelected()).toBe(true);

            $scope.selectedAll = false;

            expect($scope.isAnythingSelected()).toBe(true);
        });
    });

    describe('selectAllCallback', function () {
        beforeEach(function () {
            initializeController();
        });
        it('sets selection and calls updateContentAdSelection if checked', function () {
            $scope.selectionMenuConfig.partialSelection = true;

            spyOn($scope, 'updateContentAdSelection');
            $scope.selectionMenuConfig.selectAllCallback(true);

            expect($scope.selectedAll).toBe(true);
            expect($scope.selectedBatchId).toBe(null);
            expect($scope.selectedContentAdsStatus).toEqual({});
            expect($scope.updateContentAdSelection).toHaveBeenCalled();
            expect($scope.selectionMenuConfig.partialSelection).toBe(false);
        });

        it('sets selection and calls clearContentAdSelection if not checked', function () {
            $scope.selectionMenuConfig.partialSelection = true;

            spyOn($scope, 'clearContentAdSelection');
            $scope.selectionMenuConfig.selectAllCallback(false);

            expect($scope.selectedAll).toBe(false);
            expect($scope.selectedBatchId).toBe(null);
            expect($scope.selectedContentAdsStatus).toEqual({});
            expect($scope.clearContentAdSelection).toHaveBeenCalled();
            expect($scope.selectionMenuConfig.partialSelection).toBe(false);
        });
    });

    describe('selectBatchCallback', function () {
        beforeEach(function () {
            initializeController();
        });
        it('sets selection and calls updateContentAdSelection', function () {
            var batchId = 1;

            spyOn($scope, 'updateContentAdSelection');
            $scope.selectBatchCallback(batchId);

            expect($scope.selectedAll).toBe(false);
            expect($scope.selectedBatchId).toBe(1);
            expect($scope.selectedContentAdsStatus).toEqual({});

            expect($scope.updateContentAdSelection).toHaveBeenCalledWith();
            expect($scope.selectionMenuConfig.partialSelection).toBe(true);
        });
    });

    describe('clearContentAdSelection', function () {
        beforeEach(function () {
            initializeController();
        });
        it('unchecks all selected rows', function () {
            $scope.rows = [
                {id: 1, ad_selected: true},
                {id: 2, ad_selected: true},
                {id: 3, ad_selected: false},
            ];

            $scope.clearContentAdSelection();

            $scope.rows.forEach(function (row) {
                expect(row.ad_selected).toBe(false);
            });
        });
    });

    describe('updateContentAdSelection', function () {
        beforeEach(function () {
            initializeController();
            $scope.rows = [
                {id: 1, ad_selected: false, batch_id: 1},
                {id: 2, ad_selected: false, batch_id: 1},
                {id: 3, ad_selected: false, batch_id: 2},
            ];
        });

        it('checks all if selectedAll is true', function () {
            $scope.selectedAll = true;

            $scope.updateContentAdSelection();

            $scope.rows.forEach(function (row) {
                expect(row.ad_selected).toBe(true);
            });
        });

        it('checks all if selectedAll is true except for ads that were unchecked', function () {
            $scope.selectedAll = true;
            $scope.selectedContentAdsStatus[3] = false;

            $scope.updateContentAdSelection();

            expect($scope.rows[0].ad_selected).toBe(true);
            expect($scope.rows[1].ad_selected).toBe(true);
            expect($scope.rows[2].ad_selected).toBe(false);
        });

        it('checks all if selectedAll is true except for ads that were unchecked', function () {
            $scope.selectedAll = true;
            $scope.selectedContentAdsStatus[3] = false;

            $scope.updateContentAdSelection();

            expect($scope.rows[0].ad_selected).toBe(true);
            expect($scope.rows[1].ad_selected).toBe(true);
            expect($scope.rows[2].ad_selected).toBe(false);
        });

        it('checks batch if selectedBatchId', function () {
            $scope.selectedBatchId = 1;

            $scope.updateContentAdSelection();

            expect($scope.rows[0].ad_selected).toBe(true);
            expect($scope.rows[1].ad_selected).toBe(true);
            expect($scope.rows[2].ad_selected).toBe(false);
        });

        it('checks batch if selectedBatchId expect for ads that were unchecked', function () {
            $scope.selectedBatchId = 1;
            $scope.selectedContentAdsStatus[2] = false;

            $scope.updateContentAdSelection();

            expect($scope.rows[0].ad_selected).toBe(true);
            expect($scope.rows[1].ad_selected).toBe(false);
            expect($scope.rows[2].ad_selected).toBe(false);
        });

        it('checks batch if selectedBatchId plus all other checked ads', function () {
            $scope.selectedBatchId = 2;
            $scope.selectedContentAdsStatus[1] = true;

            $scope.updateContentAdSelection();

            expect($scope.rows[0].ad_selected).toBe(true);
            expect($scope.rows[1].ad_selected).toBe(false);
            expect($scope.rows[2].ad_selected).toBe(true);
        });

        it('checks all checked ads', function () {
            $scope.selectedContentAdsStatus[1] = true;
            $scope.selectedContentAdsStatus[2] = true;

            $scope.updateContentAdSelection();

            expect($scope.rows[0].ad_selected).toBe(true);
            expect($scope.rows[1].ad_selected).toBe(true);
            expect($scope.rows[2].ad_selected).toBe(false);
        });
    });

    describe('executeBulkAction', function () {
        beforeEach(function () {
            permissions['zemauth.can_access_table_breakdowns_feature'] = false;
            initializeController();
        });
        it('pauses all selected content ads if executeBulkAction(\'pause\')', function () {
            $scope.rows = [
                {id: 1, ad_selected: true, batch_id: 1, status_setting: constants.contentAdSourceState.ACTIVE},
                {id: 2, ad_selected: true, batch_id: 1, status_setting: constants.contentAdSourceState.ACTIVE},
                {id: 3, ad_selected: false, batch_id: 2, status_setting: constants.contentAdSourceState.ACTIVE},
            ];

            $state.params.id = 1;

            $scope.selectedContentAdsStatus[1] = true;
            $scope.selectedContentAdsStatus[2] = true;
            $scope.selectedContentAdsStatus[3] = false;

            spyOn(api.adGroupContentAdState, 'save').and.callThrough();

            $scope.executeBulkAction('pause');

            expect($scope.rows[0].status_setting).toBe(constants.contentAdSourceState.INACTIVE);
            expect($scope.rows[1].status_setting).toBe(constants.contentAdSourceState.INACTIVE);

            expect(api.adGroupContentAdState.save).toHaveBeenCalledWith(
                $state.params.id,
                constants.contentAdSourceState.INACTIVE,
                ['1', '2'],
                ['3'],
                false,
                null
            );
        });

        it('enables all selected content ads if executeBulkAction(\'resume\')', function () {
            $scope.rows = [
                {id: 1, ad_selected: true, batch_id: 1, status_setting: constants.contentAdSourceState.INACTIVE},
                {id: 2, ad_selected: true, batch_id: 1, status_setting: constants.contentAdSourceState.INACTIVE},
                {id: 3, ad_selected: false, batch_id: 2, status_setting: constants.contentAdSourceState.INACTIVE},
            ];

            $state.params.id = 1;

            $scope.selectedContentAdsStatus[1] = true;
            $scope.selectedContentAdsStatus[2] = true;
            $scope.selectedContentAdsStatus[3] = false;

            spyOn(api.adGroupContentAdState, 'save').and.callThrough();

            $scope.executeBulkAction('resume');

            expect($scope.rows[0].status_setting).toBe(constants.contentAdSourceState.ACTIVE);
            expect($scope.rows[1].status_setting).toBe(constants.contentAdSourceState.ACTIVE);

            expect(api.adGroupContentAdState.save).toHaveBeenCalledWith(
                $state.params.id,
                constants.contentAdSourceState.ACTIVE,
                ['1', '2'],
                ['3'],
                false,
                null
            );
        });

        it('downloads csv with selected content ads if executeBulkAction(\'download\')', function () {
            $scope.rows = [
                {id: 1, ad_selected: true, batch_id: 1},
                {id: 2, ad_selected: true, batch_id: 1},
                {id: 3, ad_selected: false, batch_id: 2},
            ];

            $state.params.id = 1;

            $scope.selectedContentAdsStatus[1] = true;
            $scope.selectedContentAdsStatus[2] = true;
            $scope.selectedContentAdsStatus[3] = false;

            spyOn($window, 'open');

            $scope.executeBulkAction('download');

            expect($window.open).toHaveBeenCalledWith(
                '/api/ad_groups/1/contentads/csv/?content_ad_ids_selected=1,2&content_ad_ids_not_selected=3&archived=true', // eslint-disable-line max-len
                '_blank'
            );
        });

        it('archives all selected content ads if executeBulkAction(\'archive\')', function () {
            $scope.rows = [
                {id: 1, ad_selected: true, batch_id: 1, archived: false},
                {id: 2, ad_selected: true, batch_id: 1, archived: false},
                {id: 3, ad_selected: false, batch_id: 2, archived: false},
            ];

            $scope.selectedContentAdsStatus[1] = true;
            $scope.selectedContentAdsStatus[2] = true;
            $scope.selectedContentAdsStatus[3] = false;

            spyOn(api.adGroupContentAdArchive, 'archive').and.callThrough();

            $scope.executeBulkAction('archive');

            expect(api.adGroupContentAdArchive.archive).toHaveBeenCalledWith(
                $state.params.id,
                ['1', '2'],
                ['3'],
                false,
                null
            );
        });

        it('restores all selected content ads if executeBulkAction(\'restore\')', function () {
            $scope.rows = [
                {id: 1, ad_selected: true, batch_id: 1, archived: false},
                {id: 2, ad_selected: true, batch_id: 1, archived: false},
                {id: 3, ad_selected: false, batch_id: 2, archived: false},
            ];

            $scope.selectedContentAdsStatus[1] = true;
            $scope.selectedContentAdsStatus[2] = true;
            $scope.selectedContentAdsStatus[3] = false;

            spyOn(api.adGroupContentAdArchive, 'restore').and.callThrough();

            $scope.executeBulkAction('restore');

            expect(api.adGroupContentAdArchive.restore).toHaveBeenCalledWith(
                $state.params.id,
                ['1', '2'],
                ['3'],
                false,
                null
            );
        });

        it ('does not execute a bulk action when no content ads are selected', function () {
            $scope.rows = [
                {id: 1, ad_selected: false, batch_id: 1, archived: false},
                {id: 2, ad_selected: false, batch_id: 1, archived: false},
                {id: 3, ad_selected: false, batch_id: 2, archived: false},
            ];

            $scope.selectedContentAdsStatus[1] = false;
            $scope.selectedContentAdsStatus[2] = false;
            $scope.selectedContentAdsStatus[3] = false;

            $scope.selectedAll = false;
            $scope.selectedBatchId = false;

            spyOn(api.adGroupContentAdArchive, 'restore');

            $scope.executeBulkAction('restore');

            expect(api.adGroupContentAdArchive.restore).not.toHaveBeenCalled();
        });
    });
});
