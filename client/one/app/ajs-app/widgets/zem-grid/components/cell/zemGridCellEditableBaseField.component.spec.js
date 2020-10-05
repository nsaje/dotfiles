describe('zemGridCellEditableBaseField', function() {
    var scope, element, $compileProvider, $compile, $q;

    var template =
        '<zem-grid-cell-editable-base-field ' +
        'data="ctrl.data" column="ctrl.col" row="ctrl.row" grid="ctrl.grid">' +
        '</zem-grid-cell-editable-base-field>';

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
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($rootScope, _$compile_, _$q_) {
        $compile = _$compile_;
        $q = _$q_;

        scope = $rootScope.$new();
        scope.ctrl = {};
        scope.ctrl.row = {};
        scope.ctrl.col = {};
        scope.ctrl.col.data = {};
        scope.ctrl.grid = {
            meta: {
                data: {
                    ext: {},
                },
                service: {},
                api: {
                    isSaveRequestInProgress: function() {},
                },
            },
        };
    }));

    it("should display N/A if field's value is not defined", function() {
        mockDirective('zemGridModal');

        scope.ctrl.data = undefined;
        element = $compile(template)(scope);
        scope.$digest();

        expect(element.text().trim()).toEqual('N/A');
    });

    it('should hide the field if no data is available or field is disabled in footer', function() {
        mockDirective('zemGridModal');

        delete scope.ctrl.row;
        element = $compile(template)(scope);
        scope.$digest();

        expect(element.text().trim()).toEqual('');

        element.isolateScope().ctrl.row = {};
        scope.$digest();

        expect(element.text().trim()).toEqual('N/A');

        element.isolateScope().ctrl.row = {
            level: 0,
        };
        element.isolateScope().ctrl.column.data = {
            totalRow: false,
        };
        scope.$digest();

        expect(element.text().trim()).toEqual('');
    });

    it('should not set uneditable fields to editable and add edit message instead', function() {
        mockDirective('zemGridModal');

        scope.ctrl.data = {
            isEditable: false,
            editMessage: 'Disabled',
        };
        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.isEditable).toBe(false);
        expect(element.isolateScope().ctrl.editMessage).toEqual('Disabled');
    });

    it('should set editable fields to editable', function() {
        mockDirective('zemGridModal');

        scope.ctrl.data = {
            isEditable: true,
        };
        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.isEditable).toBe(true);
    });

    it('should display autopilot icon if autopilot is on', function() {
        mockDirective('zemGridModal');
        var template =
            '<zem-grid-cell-editable-base-field ' +
            'data="ctrl.data" column="ctrl.col" row="ctrl.row" grid="ctrl.grid" show-autopilot-icon="true">' +
            '</zem-grid-cell-editable-base-field>';

        scope.ctrl.grid.meta.data = {
            level: 'ad_groups',
            breakdown: 'source',
            adGroupAutopilotState: 1,
            ext: {},
        };
        element = $compile(template)(scope);
        scope.$digest();

        expect(element.find('.auto-pilot-icon').hasClass('ng-hide')).toBe(
            false
        );
    });

    it('should hide autopilot icon if autopilot is off', function() {
        mockDirective('zemGridModal');

        scope.ctrl.grid.meta.data = {
            level: 'ad_groups',
            breakdown: 'source',
            adGroupAutopilotState: 2,
            ext: {},
        };
        scope.ctrl.row.data = {
            stats: {
                state: {
                    value: 1,
                },
            },
        };
        element = $compile(template)(scope);
        scope.$digest();

        expect(element.find('.auto-pilot-icon').hasClass('ng-hide')).toBe(true);
    });

    it('should hide autopilot icon if row is archived', function() {
        mockDirective('zemGridModal');

        scope.ctrl.grid.meta.data = {
            level: 'ad_groups',
            breakdown: 'source',
            adGroupAutopilotState: 2,
            ext: {},
        };
        scope.ctrl.row.archived = true;
        scope.ctrl.row.data = {
            stats: {
                state: {
                    value: 1,
                },
            },
        };
        element = $compile(template)(scope);
        scope.$digest();

        expect(element.find('.auto-pilot-icon').hasClass('ng-hide')).toBe(true);
    });

    it("should hide autopilot icon if row isn't active", function() {
        mockDirective('zemGridModal');

        scope.ctrl.grid.meta.data = {
            level: 'ad_groups',
            breakdown: 'source',
            adGroupAutopilotState: 2,
            ext: {},
        };
        scope.ctrl.row.data = {
            stats: {
                state: {
                    value: 2,
                },
            },
        };
        element = $compile(template)(scope);
        scope.$digest();

        expect(element.find('.auto-pilot-icon').hasClass('ng-hide')).toBe(true);
    });

    it('should call save method if input is valid', function() {
        mockDirective('zemGridModal');

        scope.ctrl.grid.meta.api.saveData = function() {};
        spyOn(scope.ctrl.grid.meta.api, 'saveData').and.callFake(function() {
            var deferred = $q.defer();
            deferred.resolve();
            return deferred.promise;
        });

        scope.ctrl.data = {
            value: 12.34,
            isEditable: true,
        };

        scope.ctrl.col.data = {
            type: 'currency',
        };

        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.editFormInputValue).toEqual('12.34');

        element.isolateScope().ctrl.editFormInputValue = 12.35;
        element.isolateScope().ctrl.filterInput();
        element.isolateScope().ctrl.save();

        expect(
            element.isolateScope().ctrl.grid.meta.api.saveData
        ).toHaveBeenCalledWith('12.35', scope.ctrl.row, scope.ctrl.col);
    });

    it("shouldn't call save method if input is invalid", function() {
        mockDirective('zemGridModal');

        scope.ctrl.grid.meta.api.saveData = function() {};
        spyOn(scope.ctrl.grid.meta.api, 'saveData').and.callFake(function() {
            var deferred = $q.defer();
            deferred.resolve();
            return deferred.promise;
        });

        scope.ctrl.data = {
            value: 12.34,
            isEditable: true,
        };

        scope.ctrl.col.data = {
            type: 'currency',
        };

        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.editFormInputValue).toEqual('12.34');

        element.isolateScope().ctrl.editFormInputValue = 'invalid';
        element.isolateScope().ctrl.filterInput();
        element.isolateScope().ctrl.save();

        expect(
            element.isolateScope().ctrl.grid.meta.api.saveData
        ).not.toHaveBeenCalled();
    });

    it("shouldn't call save method if input hasn't changed", function() {
        mockDirective('zemGridModal');

        scope.ctrl.grid.meta.api.saveData = function() {};
        spyOn(scope.ctrl.grid.meta.api, 'saveData').and.callFake(function() {
            var deferred = $q.defer();
            deferred.resolve();
            return deferred.promise;
        });

        scope.ctrl.data = {
            value: 12.34,
            isEditable: true,
        };

        scope.ctrl.col.data = {
            type: 'currency',
        };

        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.editFormInputValue).toEqual('12.34');

        element.isolateScope().ctrl.filterInput();
        element.isolateScope().ctrl.save();

        expect(
            element.isolateScope().ctrl.grid.meta.api.saveData
        ).not.toHaveBeenCalled();
    });
});
