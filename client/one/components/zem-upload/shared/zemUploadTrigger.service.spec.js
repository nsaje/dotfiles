describe('zemUploadTriggerService', function () {
    var $uibModal, zemUploadTriggerService;

    var adGroup = {
        'id': 1,
        'name': 'Test ad group',
    };

    beforeEach(module('one'));
    beforeEach(module('one.mocks.zemInitializationService'));
    beforeEach(inject(function ($injector) {
        $uibModal = $injector.get('$uibModal');
        zemUploadTriggerService = $injector.get('zemUploadTriggerService');
    }));


    it('should open upload modal', function () {
        spyOn($uibModal, 'open').and.stub();

        var onSave = function () {};
        zemUploadTriggerService.openUploadModal(adGroup, onSave);

        expect($uibModal.open).toHaveBeenCalled();
        expect($uibModal.open.calls.mostRecent().args[0].scope.adGroup).toBe(adGroup);
        expect($uibModal.open.calls.mostRecent().args[0].scope.onSave).toBe(onSave);
    });

    it('should open edit modal', function () {
        spyOn($uibModal, 'open').and.stub();

        var onSave = function () {};
        zemUploadTriggerService.openEditModal(adGroup.id, 123, [], onSave);

        expect($uibModal.open).toHaveBeenCalled();
        expect($uibModal.open.calls.mostRecent().args[0].scope.adGroupId).toBe(adGroup.id);
        expect($uibModal.open.calls.mostRecent().args[0].scope.onSave).toBe(onSave);
        expect($uibModal.open.calls.mostRecent().args[0].scope.candidates).toEqual([]);
        expect($uibModal.open.calls.mostRecent().args[0].scope.batchId).toBe(123);
    });
});
