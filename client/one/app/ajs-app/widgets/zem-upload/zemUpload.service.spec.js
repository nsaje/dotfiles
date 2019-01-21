describe('zemUploadService', function() {
    var $uibModal, zemUploadService;

    var adGroup = {
        id: 1,
        name: 'Test ad group',
    };

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function($injector) {
        $uibModal = $injector.get('$uibModal');
        zemUploadService = $injector.get('zemUploadService');
    }));

    it('should open upload modal', function() {
        spyOn($uibModal, 'open').and.callThrough();

        var onSave = function() {};
        zemUploadService.openUploadModal(adGroup, onSave);

        expect($uibModal.open).toHaveBeenCalled();
        expect($uibModal.open.calls.mostRecent().args[0].scope.adGroup).toBe(
            adGroup
        );
        expect($uibModal.open.calls.mostRecent().args[0].scope.onSave).toBe(
            onSave
        );
    });

    it('should open edit modal', function() {
        spyOn($uibModal, 'open').and.callThrough();

        var onSave = function() {};
        zemUploadService.openEditModal(adGroup.id, 123, [], onSave);

        expect($uibModal.open).toHaveBeenCalled();
        expect($uibModal.open.calls.mostRecent().args[0].scope.adGroupId).toBe(
            adGroup.id
        );
        expect($uibModal.open.calls.mostRecent().args[0].scope.onSave).toBe(
            onSave
        );
        expect(
            $uibModal.open.calls.mostRecent().args[0].scope.candidates
        ).toEqual([]);
        expect($uibModal.open.calls.mostRecent().args[0].scope.batchId).toBe(
            123
        );
    });
});
