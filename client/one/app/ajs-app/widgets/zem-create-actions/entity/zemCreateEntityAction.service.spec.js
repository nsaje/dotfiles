describe('zemCreateEntityActionService', function() {
    var zemUploadService, zemCreateEntityActionService;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($injector) {
        zemCreateEntityActionService = $injector.get(
            'zemCreateEntityActionService'
        );
        zemUploadService = $injector.get('zemUploadService');
    }));

    it('should create ContentAds using upload service', function() {
        spyOn(zemUploadService, 'openUploadModal').and.callThrough();
        var parent = {id: -1};
        zemCreateEntityActionService.createContentAds({
            type: constants.entityType.CONTENT_AD,
            parent: parent,
        });
        expect(zemUploadService.openUploadModal).toHaveBeenCalled();
    });
});
