angular.module('one').component('zemCampaignLauncherCreatives', {
    bindings: {
        stateService: '=',
    },
    template: require('./zemCampaignLauncherCreatives.component.html'),
    controller: function (zemUploadEndpointService, zemUserService) {
        var $ctrl = this;

        $ctrl.initUploadWidget = initUploadWidget;

        $ctrl.$onInit = function () {
            $ctrl.state = $ctrl.stateService.getState();
            initUploadWidget();
        };

        function initUploadWidget () {
            if ($ctrl.state.fields.uploadBatchId || $ctrl.state.requests.createCreativesBatch.inProgress) return;
            $ctrl.state.creatives.endpoint = zemUploadEndpointService.createEndpoint();
            // FIXME (jurebajt): Don't create a sample candidate on backend when creating new batch
            $ctrl.state.creatives.candidates = [];
            $ctrl.state.creatives.editFormApi = {};
            $ctrl.state.requests.createCreativesBatch = {
                inProgress: true,
            };

            var batchName = moment()
                .utc()
                .add(zemUserService.current() ? zemUserService.current().timezoneOffset : 0, 'seconds')
                .format('M/D/YYYY h:mm A');

            $ctrl.state.creatives.endpoint.createBatch(batchName)
                .then(function (response) {
                    $ctrl.state.fields.uploadBatchId = response.batchId;
                    $ctrl.state.creatives.batchName = response.batchName;
                    $ctrl.state.requests.createCreativesBatch.success = true;
                })
                .catch(function () {
                    $ctrl.state.requests.createCreativesBatch.error = true;
                })
                .finally(function () {
                    $ctrl.state.requests.createCreativesBatch.inProgress = false;
                });
        }
    },
});
