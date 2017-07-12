describe('zemUploadTrigger', function () {
    var scope, $compile, $uibModal;
    var template = '<button type="button" zem-upload-trigger ' +
                        'zem-upload-ad-group="adGroup"' +
                        'zem-upload-on-save="onUploadSave">' +
                    '</button>';
    var onUploadSave = function () {};
    var adGroup = {
        name: 'test ad group',
        id: 1,
    };

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function ($rootScope, _$compile_, _$uibModal_) {
        $compile = _$compile_;
        $uibModal = _$uibModal_;

        scope = $rootScope.$new();
        scope.onUploadSave = onUploadSave;
        scope.adGroup = adGroup;
    }));

    it('should open a modal window on click', function () {
        var element = $compile(template)(scope);

        spyOn($uibModal, 'open').and.callThrough();
        scope.$digest();

        element.click();
        expect($uibModal.open).toHaveBeenCalled();

        expect($uibModal.open.calls.mostRecent().args[0].scope.adGroup).toBe(adGroup);
        expect($uibModal.open.calls.mostRecent().args[0].scope.onSave).toBe(onUploadSave);
    });
});
