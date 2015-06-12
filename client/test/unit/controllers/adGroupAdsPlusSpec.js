'use strict';

describe('AdGroupAdsPlusCtrl', function() {
    var $scope, api, $state, $window, $q, $httpBackend;

    beforeEach(module('one'));
    beforeEach(module('stateMock'));

    beforeEach(module(function ($provide) {
        $provide.value('zemLocalStorageService', {get: function(){}})
    }));

    beforeEach(inject(function($controller, $rootScope, _api_, _$state_, _$window_) {
        $scope = $rootScope.$new();

        $scope.isPermissionInternal = function() {return true;};
        $scope.hasPermission = function() {return true;};
        $scope.getAdGroupState = function() {};
        $scope.dateRange = {};

        $scope.adGroup = {contentAdsTabWithCMS: false};

        api = _api_;

        $state = _$state_;
        $state.params = {id: 1};

        $window = _$window_;

        $controller('AdGroupAdsPlusCtrl', {$scope: $scope});
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

    describe('selectAllCallback', function() {
        it('sets selection and calls updateContentAdSelection if checked', function() {
            spyOn($scope, 'updateContentAdSelection');
            $scope.selectAllCallback(true);

            expect($scope.selectedAll).toBe(true);
            expect($scope.selectedBatchId).toBe(null);
            expect($scope.selectedContentAdsStatus).toEqual({});
            expect($scope.updateContentAdSelection).toHaveBeenCalled();
        });

        it('sets selection and calls clearContentAdSelection if not checked', function() {
            spyOn($scope, 'clearContentAdSelection');
            $scope.selectAllCallback(false);

            expect($scope.selectedAll).toBe(false);
            expect($scope.selectedBatchId).toBe(null);
            expect($scope.selectedContentAdsStatus).toEqual({});
            expect($scope.clearContentAdSelection).toHaveBeenCalled();
        });
    });

    describe('selectThisPageCallback', function() {
        it('sets selection and calls updateContentAdSelection', function() {
            $scope.rows = [{id: 1}];

            spyOn($scope, 'updateContentAdSelection');
            $scope.selectThisPageCallback();

            expect($scope.selectedAll).toBe(false);
            expect($scope.selectedBatchId).toBe(null);
            expect($scope.selectedContentAdsStatus).toEqual({1: true});

            expect($scope.updateContentAdSelection).toHaveBeenCalledWith();
        });
    });

    describe('selectBatchCallback', function() {
        it('sets selection and calls updateContentAdSelection', function() {
            var batchId = 1;

            spyOn($scope, 'updateContentAdSelection');
            $scope.selectBatchCallback(batchId);

            expect($scope.selectedAll).toBe(false);
            expect($scope.selectedBatchId).toBe(1);
            expect($scope.selectedContentAdsStatus).toEqual({});

            expect($scope.updateContentAdSelection).toHaveBeenCalledWith();
        });
    });

    describe('clearContentAdSelection', function() {
        it('unchecks all selected rows', function() {
            $scope.rows = [
                {id: 1, ad_selected: true},
                {id: 2, ad_selected: true},
                {id: 3, ad_selected: false}
            ];

            $scope.clearContentAdSelection();

            $scope.rows.forEach(function(row) {
                expect(row.ad_selected).toBe(false);
            });
        });
    });

    describe('updateContentAdSelection', function() {
        beforeEach(function() {
            $scope.rows = [
                {id: 1, ad_selected: false, batch_id: 1},
                {id: 2, ad_selected: false, batch_id: 1},
                {id: 3, ad_selected: false, batch_id: 2}
            ];
        });

        it('checks all if selectedAll is true', function() {
            $scope.selectedAll = true;

            $scope.updateContentAdSelection();

            $scope.rows.forEach(function(row) {
                expect(row.ad_selected).toBe(true);
            });
        });

        it('checks all if selectedAll is true except for ads that were unchecked', function() {
            $scope.selectedAll = true;
            $scope.selectedContentAdsStatus[3] = false;

            $scope.updateContentAdSelection();

            expect($scope.rows[0].ad_selected).toBe(true);
            expect($scope.rows[1].ad_selected).toBe(true);
            expect($scope.rows[2].ad_selected).toBe(false);
        });

        it('checks all if selectedAll is true except for ads that were unchecked', function() {
            $scope.selectedAll = true;
            $scope.selectedContentAdsStatus[3] = false;

            $scope.updateContentAdSelection();

            expect($scope.rows[0].ad_selected).toBe(true);
            expect($scope.rows[1].ad_selected).toBe(true);
            expect($scope.rows[2].ad_selected).toBe(false);
        });

        it('checks batch if selectedBatchId', function() {
            $scope.selectedBatchId = 1;

            $scope.updateContentAdSelection();

            expect($scope.rows[0].ad_selected).toBe(true);
            expect($scope.rows[1].ad_selected).toBe(true);
            expect($scope.rows[2].ad_selected).toBe(false);
        });

        it('checks batch if selectedBatchId expect for ads that were unchecked', function() {
            $scope.selectedBatchId = 1;
            $scope.selectedContentAdsStatus[2] = false;

            $scope.updateContentAdSelection();

            expect($scope.rows[0].ad_selected).toBe(true);
            expect($scope.rows[1].ad_selected).toBe(false);
            expect($scope.rows[2].ad_selected).toBe(false);
        });

        it('checks batch if selectedBatchId plus all other checked ads', function() {
            $scope.selectedBatchId = 2;
            $scope.selectedContentAdsStatus[1] = true;

            $scope.updateContentAdSelection();

            expect($scope.rows[0].ad_selected).toBe(true);
            expect($scope.rows[1].ad_selected).toBe(false);
            expect($scope.rows[2].ad_selected).toBe(true);
        });

        it('checks all checked ads', function() {
            $scope.selectedContentAdsStatus[1] = true;
            $scope.selectedContentAdsStatus[2] = true;

            $scope.updateContentAdSelection();

            expect($scope.rows[0].ad_selected).toBe(true);
            expect($scope.rows[1].ad_selected).toBe(true);
            expect($scope.rows[2].ad_selected).toBe(false);
        });
    });

    describe('executeBulkAction', function() {
        it('pauses all selected content ads if selectedBulkAction == \'pause\'', function() {
            $scope.rows = [
                {id: 1, ad_selected: true, batch_id: 1, status_setting: constants.contentAdSourceState.ACTIVE},
                {id: 2, ad_selected: true, batch_id: 1, status_setting: constants.contentAdSourceState.ACTIVE},
                {id: 3, ad_selected: false, batch_id: 2, status_setting: constants.contentAdSourceState.ACTIVE}
            ];

            $state.params.id = 1;

            $scope.selectedContentAdsStatus[1] = true;
            $scope.selectedContentAdsStatus[2] = true;
            $scope.selectedContentAdsStatus[3] = false;

            $scope.selectedBulkAction = 'pause';

            spyOn(api.adGroupContentAdState, 'save').and.callThrough();

            $scope.executeBulkAction();

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

        it('enables all selected content ads if selectedBulkAction == \'resume\'', function() {
            $scope.rows = [
                {id: 1, ad_selected: true, batch_id: 1, status_setting: constants.contentAdSourceState.INACTIVE},
                {id: 2, ad_selected: true, batch_id: 1, status_setting: constants.contentAdSourceState.INACTIVE},
                {id: 3, ad_selected: false, batch_id: 2, status_setting: constants.contentAdSourceState.INACTIVE}
            ];

            $state.params.id = 1;

            $scope.selectedContentAdsStatus[1] = true;
            $scope.selectedContentAdsStatus[2] = true;
            $scope.selectedContentAdsStatus[3] = false;

            $scope.selectedBulkAction = 'resume';

            spyOn(api.adGroupContentAdState, 'save').and.callThrough();

            $scope.executeBulkAction();

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

        it('downloads csv with selected content ads if selectedBulkAction == \'download\'', function() {
            $scope.rows = [
                {id: 1, ad_selected: true, batch_id: 1},
                {id: 2, ad_selected: true, batch_id: 1},
                {id: 3, ad_selected: false, batch_id: 2}
            ];

            $state.params.id = 1;

            $scope.selectedContentAdsStatus[1] = true;
            $scope.selectedContentAdsStatus[2] = true;
            $scope.selectedContentAdsStatus[3] = false;

            spyOn($window, 'open');

            $scope.selectedBulkAction = 'download';
            $scope.executeBulkAction();

            expect($window.open).toHaveBeenCalledWith(
                '/api/ad_groups/1/contentads/csv/?content_ad_ids_enabled=1,2&content_ad_ids_disabled=3',
                '_blank'
            );
        });
    });
});
