describe('zemGridCellEditButton', function() {
    var scope, element, $compile, $q, zemUploadService;

    var template =
        '<zem-grid-cell-edit-button data="ctrl.data" row="ctrl.row" column="ctrl.col" grid="ctrl.grid">' +
        '</zem-grid-cell-edit-button>';

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function(
        $rootScope,
        _$compile_,
        _$q_,
        _zemUploadService_
    ) {
        zemUploadService = _zemUploadService_;
        $compile = _$compile_;
        $q = _$q_;

        scope = $rootScope.$new();
        scope.ctrl = {};
        scope.ctrl.grid = {
            meta: {
                data: {
                    id: 11,
                    level: '',
                    breakdown: '',
                    ext: {},
                },
                dataService: {
                    editRow: function() {},
                },
                api: {
                    loadData: function() {},
                },
            },
        };
    }));

    beforeEach(inject(function($httpBackend) {
        $httpBackend.when('GET', '/api/users/current/').respond({});
        $httpBackend.when('GET', '/api/all_accounts/nav/').respond({});
    }));

    it('should display state selector field ordinary rows', function() {
        scope.ctrl.row = {
            level: 1,
            data: {},
        };

        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.isFieldVisible).toBe(true);
    });

    it('should hide state selector field footer', function() {
        scope.ctrl.row = {
            level: 0,
            data: {},
        };

        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.isFieldVisible).toBe(false);
    });

    it('should make a call and open modal when clicked', function() {
        spyOn(scope.ctrl.grid.meta.dataService, 'editRow').and.callFake(
            function() {
                var deferred = $q.defer();
                deferred.resolve({
                    data: {
                        batch_id: 123,
                        candidates: [],
                    },
                });
                return deferred.promise;
            }
        );
        spyOn(zemUploadService, 'openEditModal').and.stub();

        element = $compile(template)(scope);
        scope.$digest();

        element.find('button').click();
        expect(zemUploadService.openEditModal).toHaveBeenCalled();
    });
});
