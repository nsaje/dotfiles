angular
    .module('one.widgets')
    .service('zemCloneCampaignService', function($uibModal) {
        this.openCloneModal = openCloneModal;
        this.openResultsModal = openResultsModal;

        function openCloneModal(campaignId, campaignName) {
            console.log(campaignName);
            var modal = $uibModal.open({
                component: 'zemCloneCampaignModal',
                backdrop: 'static',
                keyboard: false,
                resolve: {
                    campaign: {
                        id: campaignId,
                        name: campaignName,
                    },
                },
            });

            return modal.result;
        }

        function openResultsModal(campaign) {
            var modal = $uibModal.open({
                component: 'zemCloneCampaignSuccessfulModal',
                backdrop: 'static',
                keyboard: false,
                resolve: {
                    campaign: campaign,
                },
            });

            return modal.result;
        }
    });
