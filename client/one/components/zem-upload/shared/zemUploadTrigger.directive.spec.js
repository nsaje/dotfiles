/* globals describe, beforeEach, inject, module, it, expect, spyOn */
describe('zemUploadTrigger', function () {
    var scope, $compile, $modal;
    var template = '<button type="button" zem-upload-trigger zem-upload-ad-group="adGroup" zem-upload-on-save="onUploadSave"></button>';
    var onUploadSave = function () {};
    var adGroup = {
        name: 'test ad group',
        id: 1,
    };

    beforeEach(module('one'));
    beforeEach(inject(function ($rootScope, _$compile_, _$modal_) {
        $compile = _$compile_;
        $modal = _$modal_;

        scope = $rootScope.$new();
        scope.onUploadSave = onUploadSave;
        scope.adGroup = adGroup;
    }));

    it('should open a modal window on click', function () {
        var element = $compile(template)(scope);

        spyOn($modal, 'open').and.stub();
        scope.$digest();

        element.click();
        expect($modal.open).toHaveBeenCalled();

        expect($modal.open.calls.mostRecent().args[0].scope.adGroup).toBe(adGroup);
        expect($modal.open.calls.mostRecent().args[0].scope.onSave).toBe(onUploadSave);
    });
});
