'use strict'

describe('UploadAdsModalCtrl', function() {
    var $scope;

    beforeEach(module('one'));

    beforeEach(inject(function($controller, $rootScope) {
        $scope = $rootScope.$new();
        $controller('UploadAdsModalController', {$scope: $scope});
    }));


});
