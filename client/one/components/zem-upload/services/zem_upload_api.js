/* globals oneApp */
/* eslint-disable camelcase */
'use strict';

oneApp.factory('zemUploadApi', ['$modal', '$rootScope', function ($modal, $rootScope) {

    function UploadApi () {
        this.openModal = openModal;

        function openModal (adGroup, apiEndpoint) {
            var scope = $rootScope.$new();
            scope.adGroup = adGroup;
            scope.api = apiEndpoint;

            return $modal.open({
                templateUrl: '/components/zem-upload/templates/zem_upload.html',
                controller: 'zemUploadModalCtrl',
                windowClass: 'modal-content-upload',
                scope: scope,
            });
        }
    }

    return {
        createInstance: function () {
            return new UploadApi();
        },
    };
}]);
