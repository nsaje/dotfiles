require('./zemCampaignLauncherCreatives.component.less');

angular.module('one').component('zemCampaignLauncherCreatives', {
    bindings: {
        stateService: '=',
    },
    template: require('./zemCampaignLauncherCreatives.component.html'),
    controller: function(zemUploadEndpointService, zemUserService) {
        var $ctrl = this;

        $ctrl.initUploadWidget = initUploadWidget;

        $ctrl.$onInit = function() {
            $ctrl.state = $ctrl.stateService.getState();
            $ctrl.campaignObjective = constants.campaignObjective;
            initUploadWidget();
        };

        function initUploadWidget() {
            if (
                $ctrl.state.fields.uploadBatch ||
                $ctrl.state.requests.createCreativesBatch.inProgress
            )
                return;
            $ctrl.state.creatives.endpoint = zemUploadEndpointService.createEndpoint();
            $ctrl.state.creatives.editFormApi = {};
            $ctrl.state.requests.createCreativesBatch = {
                inProgress: true,
            };

            var batchName = moment()
                .utc()
                .add(
                    zemUserService.current()
                        ? zemUserService.current().timezoneOffset
                        : 0,
                    'seconds'
                )
                .format('M/D/YYYY h:mm A');
            var withoutCandidates = true;
            $ctrl.state.creatives.endpoint
                .createBatch(batchName, withoutCandidates)
                .then(function(response) {
                    $ctrl.state.fields.uploadBatch = response.batchId;
                    $ctrl.state.creatives.batchName = response.batchName;
                    $ctrl.state.creatives.candidates = response.candidates;
                    $ctrl.state.requests.createCreativesBatch.success = true;
                })
                .catch(function() {
                    $ctrl.state.requests.createCreativesBatch.error = true;
                })
                .finally(function() {
                    $ctrl.state.requests.createCreativesBatch.inProgress = false;
                });
        }
    },
});
