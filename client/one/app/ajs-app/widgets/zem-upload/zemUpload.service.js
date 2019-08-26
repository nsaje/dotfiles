angular
    .module('one.widgets')
    .service('zemUploadService', function(
        $uibModal,
        $rootScope,
        zemUploadEndpointService,
        zemNavigationNewService
    ) {
        //
        // Public API
        //
        this.openUploadModal = openUploadModal;
        this.openEditModal = openEditModal;

        function getShowVideoUpload() {
            var campaign = zemNavigationNewService.getActiveEntityByType(
                constants.entityType.CAMPAIGN
            );
            return (
                campaign && campaign.data.type === constants.campaignTypes.VIDEO
            );
        }

        function getShowDisplayUpload() {
            var campaign = zemNavigationNewService.getActiveEntityByType(
                constants.entityType.CAMPAIGN
            );
            return (
                campaign &&
                campaign.data.type === constants.campaignTypes.DISPLAY
            );
        }

        function openUploadModal(adGroup, onSave) {
            var modalScope = $rootScope.$new();
            modalScope.adGroup = adGroup;
            modalScope.onSave = onSave;
            modalScope.showVideoUpload = getShowVideoUpload();
            modalScope.showDisplayUpload = getShowDisplayUpload();

            var modal = $uibModal.open({
                template:
                    '<zem-upload ad-group="adGroup" on-save="onSave" close-modal="closeModal" show-video-upload="showVideoUpload" show-display-upload="showDisplayUpload"></zem-upload>',
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
            modalScope.showVideoUpload = getShowVideoUpload();
            modalScope.showDisplayUpload = getShowDisplayUpload();

            var modal = $uibModal.open({
                template:
                    '<zem-upload-step2 ad-group-id="adGroupId" callback="cb()" close="$close" ' +
                    'is-edit="true" candidates="candidates" batch-id="batchId" endpoint="endpoint" ' +
                    'auto-open-edit-form="true" show-video-upload="showVideoUpload" show-display-upload="showDisplayUpload">' +
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
