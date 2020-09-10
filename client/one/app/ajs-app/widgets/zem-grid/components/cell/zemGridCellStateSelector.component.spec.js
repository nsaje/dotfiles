describe('zemGridCellStateSelector', function() {
    var scope, element, $compile, $q;

    var template =
        '<zem-grid-cell-state-selector data="ctrl.data" row="ctrl.row" column="ctrl.col" grid="ctrl.grid">' +
        '</zem-grid-cell-state-selector>';

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($rootScope, _$compile_, _$q_) {
        $compile = _$compile_;
        $q = _$q_;

        scope = $rootScope.$new();
        scope.ctrl = {};
        scope.ctrl.grid = {
            meta: {
                data: {
                    level: '',
                    breakdown: '',
                    ext: {},
                },
                dataService: {
                    isSaveRequestInProgress: function() {},
                },
            },
        };
        scope.ctrl.row = {
            data: {},
        };
    }));

    it('should set undefined available state values for invalid level or breakdown', function() {
        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.stateValues).toEqual({
            enabled: undefined,
            paused: undefined,
        });
    });

    it('should correctly set available state values based on level and breakdown', function() {
        var tests = [
            // TODO: Add tests for other level-breakdown combinations
            {
                level: 'campaigns',
                breakdown: 'ad_group',
                expectedResult: {enabled: 1, paused: 2},
            },
        ];

        tests.forEach(function(test) {
            scope.ctrl.grid = {
                meta: {
                    data: {
                        level: test.level,
                        breakdown: test.breakdown,
                        ext: {},
                    },
                    dataService: {
                        isSaveRequestInProgress: function() {},
                    },
                },
            };

            element = $compile(template)(scope);
            scope.$digest();

            expect(element.isolateScope().ctrl.stateValues).toEqual(
                test.expectedResult
            );
        });
    });

    it('should display state selector field in rows on first level', function() {
        scope.ctrl.row = {
            level: 1,
            data: {},
        };

        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.isFieldVisible).toBe(true);
    });

    it('should hide state selector field in rows on levels > 1', function() {
        scope.ctrl.row = {
            level: 2,
            data: {},
        };

        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.isFieldVisible).toBe(false);
    });

    it('should correctly determine if current state is active', function() {
        var tests = [
            {value: 1, expectedResult: true},
            {value: 2, expectedResult: false},
        ];

        tests.forEach(function(test) {
            element = $compile(template)(scope);
            scope.$digest();

            element.isolateScope().ctrl.stateValues = {enabled: 1};
            scope.ctrl.data = {
                value: test.value,
            };
            scope.$digest();

            expect(element.isolateScope().ctrl.active).toBe(
                test.expectedResult
            );
        });
    });

    it('should update state selector field on row or data change', function() {
        scope.ctrl.row = {
            level: 1,
            data: {},
        };

        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.isFieldVisible).toBe(true);

        scope.ctrl.row = {
            level: 2,
            data: {},
        };
        scope.$digest();

        expect(element.isolateScope().ctrl.isFieldVisible).toBe(false);

        element.isolateScope().ctrl.stateValues = {enabled: 1};
        scope.ctrl.data = {
            value: 1,
        };
        scope.$digest();

        expect(element.isolateScope().ctrl.active).toBe(true);

        scope.ctrl.data = {
            value: 2,
        };
        scope.$digest();

        expect(element.isolateScope().ctrl.active).toBe(false);
    });

    it('should not make a save request if state is not active and enabling is disabled by autopilot', function() {
        scope.ctrl.grid.meta.dataService.saveData = function() {};
        spyOn(scope.ctrl.grid.meta.dataService, 'saveData').and.callFake(
            function() {
                var deferred = $q.defer();
                deferred.resolve(false);
                return deferred.promise;
            }
        );
        scope.ctrl.data = {
            value: 1,
            isEditable: true,
        };
        scope.ctrl.grid.meta.data.enablingAutopilotSourcesAllowed = false;

        element = $compile(template)(scope);
        scope.$digest();

        element.isolateScope().ctrl.active = false;
        element.isolateScope().ctrl.modal = null;
        element.isolateScope().ctrl.setState(2);

        expect(
            element.isolateScope().ctrl.grid.meta.dataService.saveData
        ).not.toHaveBeenCalled();
    });

    it('should make a save request if source is in group', function() {
        scope.ctrl.grid.meta.dataService.saveData = function() {};
        spyOn(scope.ctrl.grid.meta.dataService, 'saveData').and.callFake(
            function() {
                var deferred = $q.defer();
                deferred.resolve(false);
                return deferred.promise;
            }
        );
        scope.ctrl.data = {
            value: 1,
            isEditable: true,
        };
        scope.ctrl.grid.meta.data.enablingAutopilotSourcesAllowed = false;
        scope.ctrl.row.inGroup = true;

        element = $compile(template)(scope);
        scope.$digest();

        element.isolateScope().ctrl.active = false;
        element.isolateScope().ctrl.modal = null;
        element.isolateScope().ctrl.setState(2);

        expect(
            element.isolateScope().ctrl.grid.meta.dataService.saveData
        ).toHaveBeenCalled();
    });

    it('should not make a save request if field is not editable', function() {
        scope.ctrl.grid.meta.dataService.saveData = function() {};
        spyOn(scope.ctrl.grid.meta.dataService, 'saveData').and.callFake(
            function() {
                var deferred = $q.defer();
                deferred.resolve(false);
                return deferred.promise;
            }
        );
        scope.ctrl.data = {
            value: 1,
            isEditable: false,
        };

        element = $compile(template)(scope);
        scope.$digest();

        element.isolateScope().ctrl.active = true;
        element.isolateScope().ctrl.modal = null;
        element.isolateScope().ctrl.setState(2);

        expect(
            element.isolateScope().ctrl.grid.meta.dataService.saveData
        ).not.toHaveBeenCalled();
    });

    it('should make a save request if field is editable', function() {
        scope.ctrl.grid.meta.dataService.saveData = function() {};
        spyOn(scope.ctrl.grid.meta.dataService, 'saveData').and.callFake(
            function() {
                var deferred = $q.defer();
                deferred.resolve(false);
                return deferred.promise;
            }
        );
        scope.ctrl.data = {
            value: 1,
            isEditable: true,
        };

        element = $compile(template)(scope);
        scope.$digest();

        element.isolateScope().ctrl.active = true;
        element.isolateScope().ctrl.modal = null;
        element.isolateScope().ctrl.setState(2);

        expect(
            element.isolateScope().ctrl.grid.meta.dataService.saveData
        ).toHaveBeenCalled();
    });
});
