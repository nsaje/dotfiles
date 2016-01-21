'use strict';

describe('ActionLogCtrl', function () {
    var $scope, ctrl;

    beforeEach(function () {
        module('actionlog');

        inject(function ($rootScope, $controller) {
            $scope = $rootScope.$new();
            ctrl = $controller('ActionLogCtrl', {$scope: $scope});
        });
    });

    it('should init without problems', function () {
        expect(ctrl).toBeDefined();
    });
});
