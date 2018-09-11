describe('zemGridCellBidModifierField', function() {
    var scope, element, $compileProvider, $compile, $q; // eslint-disable-line

    var template =
        '<zem-grid-cell-bid-modifier-field ' +
        'data="ctrl.data" column="ctrl.col" row="ctrl.row" grid="ctrl.grid">' +
        '</zem-grid-cell-bid-modifier-field>';

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

    beforeEach(inject(function($rootScope, _$compile_, _$q_) {
        $compile = _$compile_;
        $q = _$q_; // eslint-disable-line

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
                dataService: {
                    isSaveRequestInProgress: function() {},
                },
            },
        };
    }));

    it("should display N/A and not be editable if publisher is 'all publishers'", function() {
        mockDirective('zemGridModal');

        scope.ctrl.row.id = 'all publishers__4';
        element = $compile(template)(scope);
        scope.$digest();

        expect(element.text().trim()).toEqual('N/A');
    });

    it("should display 0.00% if field's value is not defined", function() {
        mockDirective('zemGridModal');

        scope.ctrl.data = undefined;
        element = $compile(template)(scope);
        scope.$digest();

        expect(element.text().trim()).toEqual('0.00%');
    });
});
