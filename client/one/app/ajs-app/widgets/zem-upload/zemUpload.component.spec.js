describe('zemUpload', function() {
    var scope, $compileProvider, $compile;
    var template =
        '<zem-upload data-ad-group="ctrl.adGroup" data-on-save="ctrl.onSave" data-close-modal="ctrl.nop">' +
        '</zem-upload>';
    var onUploadSave = function() {};
    var adGroup = {
        name: 'test ad group',
        id: 1,
    };

    function mockDirective(directive) {
        $compileProvider.directive(directive, function() {
            return {
                priority: 100000,
                terminal: true,
                link: function() {},
            };
        });
    }

    beforeEach(
        angular.mock.module('one', function(_$compileProvider_) {
            $compileProvider = _$compileProvider_;
        })
    );
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($rootScope, _$compile_) {
        $compile = _$compile_;
        scope = $rootScope.$new();
        scope.ctrl = {};
        scope.ctrl.nop = function() {};
        scope.ctrl.adGroup = adGroup;
        scope.ctrl.onSave = onUploadSave;
    }));

    it('should render step 0 directive on load', function() {
        mockDirective('zemUploadStep0');
        mockDirective('zemUploadStep1');
        mockDirective('zemUploadStep2');
        mockDirective('zemUploadStep3');

        var element = $compile(template)(scope);
        scope.$digest();

        element.isolateScope().ctrl.step = 0;
        scope.$digest();

        expect(element.find('zem-upload-step0').length).toBe(1);
    });

    it('should render step 1 directive on load', function() {
        mockDirective('zemUploadStep1');
        mockDirective('zemUploadStep2');
        mockDirective('zemUploadStep3');

        var element = $compile(template)(scope);
        scope.$digest();

        expect(element.find('zem-upload-step1').length).toBe(1);
    });

    it('should render step 2', function() {
        mockDirective('zemUploadStep1');
        mockDirective('zemUploadStep2');
        mockDirective('zemUploadStep3');

        var element = $compile(template)(scope);
        scope.$digest();

        element.isolateScope().ctrl.step = 2;
        scope.$digest();

        expect(element.find('zem-upload-step2').length).toBe(1);
    });

    it('should render step 3 and pass parameters', function() {
        mockDirective('zemUploadStep1');
        mockDirective('zemUploadStep2');
        mockDirective('zemUploadStep3');

        var element = $compile(template)(scope);
        scope.$digest();

        element.isolateScope().ctrl.step = 3;
        scope.$digest();

        expect(element.find('zem-upload-step3').length).toBe(1);
    });
});

describe('ZemUploadCtrl', function() {
    var zemUploadEndpointService, ctrl, mockEndpoint;
    var adGroup = {
        name: 'test ad group',
        id: 1,
    };
    var onUploadSave = function() {};

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(inject(function(
        $rootScope,
        _zemUploadEndpointService_,
        $controller
    ) {
        zemUploadEndpointService = _zemUploadEndpointService_;

        mockEndpoint = {};
        spyOn(zemUploadEndpointService, 'createEndpoint').and.returnValue(
            mockEndpoint
        );

        var mockedDate = new Date(Date.UTC(2016, 6, 1, 15, 5));
        jasmine.clock().mockDate(mockedDate);

        var scope = $rootScope.$new();
        ctrl = $controller(
            'ZemUploadCtrl',
            {
                $scope: scope,
            },
            {
                nop: function() {},
                adGroup: adGroup,
                onSave: onUploadSave,
            }
        );
    }));

    it('uses current datetime as default batch name', function() {
        expect(ctrl.defaultBatchName).toEqual('7/1/2016 3:05 PM');
    });

    it('should initialize correctly', function() {
        expect(zemUploadEndpointService.createEndpoint).toHaveBeenCalledWith(
            adGroup.id
        );
        expect(ctrl.endpoint).toBe(mockEndpoint);
        expect(ctrl.step).toBe(0);
    });

    it('should switch to step 2 and store parameters', function() {
        var batchId = 1;
        var batchName = 'mock batch';
        var candidates = [];
        ctrl.switchToContentAdPicker(batchId, batchName, candidates);

        expect(ctrl.step).toBe(2);
        expect(ctrl.batchId).toBe(batchId);
        expect(ctrl.batchName).toBe(batchName);
        expect(ctrl.candidates).toBe(candidates);
    });

    it('should switch to step 3 and store parameters', function() {
        var numSuccessful = 1;
        ctrl.switchToSuccessScreen(numSuccessful);

        expect(ctrl.step).toBe(3);
        expect(ctrl.numSuccessful).toBe(numSuccessful);
    });
});
