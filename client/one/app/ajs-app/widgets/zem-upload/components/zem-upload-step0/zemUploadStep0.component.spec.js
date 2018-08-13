describe('ZemUploadStep0Ctrl', function() {
    var scope, $q, ctrl;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function($controller, $rootScope, _$q_) {
        $q = _$q_;
        scope = $rootScope.$new();
        var mockEndpoint = {
            createBatch: function() {},
        };

        ctrl = $controller(
            'ZemUploadStep0Ctrl',
            {$scope: scope},
            {
                endpoint: mockEndpoint,
                defaultBatchName: 'default batch name',
                singleUploadCallback: function() {},
                csvUploadCallback: function() {},
                close: function() {},
            }
        );
    }));

    it('switches to single content ad upload', function() {
        var deferred = $q.defer();
        spyOn(ctrl.endpoint, 'createBatch').and.callFake(function() {
            return deferred.promise;
        });

        spyOn(ctrl, 'singleUploadCallback').and.stub();
        ctrl.switchToSingleContentAdUpload();

        deferred.resolve({
            batchId: 1234,
            batchName: 'batch name',
            candidates: [
                {
                    id: 1,
                    title: 'ad title',
                },
            ],
        });
        scope.$digest();

        expect(ctrl.singleUploadCallback).toHaveBeenCalledWith({
            batchId: 1234,
            batchName: 'batch name',
            candidates: [
                {
                    id: 1,
                    title: 'ad title',
                },
            ],
            autoOpenEditForm: true,
        });
    });

    it('switches to csv upload', function() {
        spyOn(ctrl, 'csvUploadCallback').and.stub();
        ctrl.switchToCsvUpload();
        expect(ctrl.csvUploadCallback).toHaveBeenCalled();
    });
});
