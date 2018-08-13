angular
    .module('one.widgets')
    .service('zemUploadService', function(
        $uibModal,
        $rootScope,
        zemUploadEndpointService
    ) {
        //
        // Public API
        //
        this.openUploadModal = openUploadModal;
        this.openEditModal = openEditModal;

        function openUploadModal(adGroup, onSave) {
            var modalScope = $rootScope.$new();
            modalScope.adGroup = adGroup;
            modalScope.onSave = onSave;

            var modal = $uibModal.open({
                template:
                    '<zem-upload ad-group="adGroup" on-save="onSave" close-modal="closeModal"></zem-upload>',
                controller: function($scope) {
                    $scope.closeModal = $scope.$close;
                },
                backdrop: 'static',
                keyboard: false,
                windowClass: 'content-upload',
                scope: modalScope,
            });

            return modal.result;
        }

        function openEditModal(adGroupId, batchId, candidates, onSave) {
            var modalScope = $rootScope.$new();
            modalScope.adGroupId = adGroupId;
            modalScope.batchId = batchId;
            modalScope.candidates = candidates;
            modalScope.endpoint = zemUploadEndpointService.createEndpoint(
                modalScope.adGroupId
            );
            modalScope.onSave = onSave;

            var modal = $uibModal.open({
                template:
                    '<zem-upload-step2 ad-group-id="adGroupId" callback="cb()" close="$close" ' +
                    'is-edit="true" candidates="candidates" batch-id="batchId" endpoint="endpoint" ' +
                    'auto-open-edit-form="true">' +
                    '</zem-upload-step2>',
                controller: function($scope) {
                    $scope.cb = function() {
                        $scope.onSave();
                        $scope.$close();
                    };
                },
                backdrop: 'static',
                keyboard: false,
                windowClass: 'content-upload',
                scope: modalScope,
            });

            return modal.result;
        }
    });
