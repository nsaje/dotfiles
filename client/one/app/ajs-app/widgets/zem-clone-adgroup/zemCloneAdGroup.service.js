angular
    .module('one.widgets')
    .service('zemCloneAdGroupService', function(
        $uibModal,
        zemCloneAdGroupEndpoint
    ) {
        //eslint-disable-line max-len

        this.openCloneModal = openCloneModal;
        this.openResultsModal = openResultsModal;
        this.clone = clone;

        function openCloneModal(campaignId, adGroupId) {
            var modal = $uibModal.open({
                component: 'zemCloneAdGroupModal',
                backdrop: 'static',
                keyboard: false,
                resolve: {
                    campaignId: campaignId,
                    adGroupId: adGroupId,
                },
            });

            return modal.result;
        }

        function clone(adGroupId, data) {
            return zemCloneAdGroupEndpoint.clone(adGroupId, data);
        }

        function openResultsModal(
            adGroup,
            destinationCampaign,
            destinationAdGroup
        ) {
            var modal = $uibModal.open({
                component: 'zemCloneAdGroupSuccessfulModal',
                backdrop: 'static',
                keyboard: false,
                resolve: {
                    adGroup: adGroup,
                    destinationCampaign: destinationCampaign,
                    destinationAdGroup: destinationAdGroup,
                },
            });

            return modal.result;
        }
    });
