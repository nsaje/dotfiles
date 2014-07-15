'use strict';

describe('MainCtrl', function () {
    var scope, ctrl;

    beforeEach(module('one'));

    beforeEach(inject(function ($rootScope, $controller) {
        scope = $rootScope.$new();
        ctrl = $controller('MainCtrl', {$scope: scope});
    }));

    it('should init accounts to empty array', function () {
        expect(scope.accounts).toBe(null);
    });
});
