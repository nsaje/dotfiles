/* globals angular,moment,constants */
angular.module('one.widgets').component('zemPublisherGroups', {
    templateUrl: '/app/widgets/zem-publisher-groups/zemPublisherGroups.component.html',
    bindings: {
        account: '<',
    },
    controller: function ($filter, zemPublisherGroupsEndpoint) {
        var $ctrl = this;

        $ctrl.showCollapsed = false;
        $ctrl.loading = true;

        $ctrl.download = download;

        $ctrl.$onInit = function () {
            zemPublisherGroupsEndpoint.get($ctrl.account.id).then(function (data) {
                $ctrl.publisherGroups = data;
                $ctrl.loading = false;
            });
        };

        function download (publisherGroupId) {
            zemPublisherGroupsEndpoint.download($ctrl.account.id, publisherGroupId);
        }
    },
});