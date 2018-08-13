describe('zemGridCellPerformanceIndicator', function() {
    var scope, element, $compile;

    var template =
        '<zem-grid-cell-performance-indicator data="ctrl.data" row="ctrl.row"></zem-grid-cell-performance-indicator>'; // eslint-disable-line max-len

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function($rootScope, _$compile_) {
        $compile = _$compile_;

        scope = $rootScope.$new();
        scope.ctrl = {};
    }));

    it('should set performance icon to neutral emoticon by default', function() {
        element = $compile(template)(scope);
        scope.$digest();

        expect(element.isolateScope().ctrl.overall).toEqual({
            file: 'emoticon-neutral-gray.svg',
            class: 'img-icon-neutral',
        });
    });

    it('should correctly set field visibility', function() {
        var tests = [
            {rowLevel: 1, expectedResult: true},
            {rowLevel: 2, expectedResult: true},
            {rowLevel: 0, expectedResult: false},
        ];

        tests.forEach(function(test) {
            scope.ctrl.row = {
                level: test.rowLevel,
            };

            element = $compile(template)(scope);
            scope.$digest();

            expect(element.isolateScope().ctrl.isFieldVisible).toBe(
                test.expectedResult
            );
        });
    });

    it('should correctly set performance icon', function() {
        var tests = [
            {
                overall: 1,
                expectedResult: {
                    file: 'emoticon-happy-green.svg',
                    class: 'img-icon-happy',
                },
            },
            {
                overall: 2,
                expectedResult: {
                    file: 'emoticon-neutral-gray.svg',
                    class: 'img-icon-neutral',
                },
            },
            {
                overall: 3,
                expectedResult: {
                    file: 'emoticon-sad-red.svg',
                    class: 'img-icon-sad',
                },
            },
        ];

        tests.forEach(function(test) {
            scope.ctrl.data = {
                overall: test.overall,
            };

            element = $compile(template)(scope);
            scope.$digest();

            expect(element.isolateScope().ctrl.overall).toEqual(
                test.expectedResult
            );
        });
    });

    it('should correctly set performance icon image src and class', inject(function(
        config
    ) {
        scope.ctrl.data = {
            overall: 1,
        };

        element = $compile(template)(scope);
        scope.$digest();

        var iconElement = element.find('.zem-icon');

        expect(iconElement.hasClass('img-icon-happy')).toBe(true);
        expect(iconElement.attr('src')).toEqual(
            config.staticUrl + '/one/images/emoticon-happy-green.svg'
        );
    }));
});
