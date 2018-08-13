require('./zemPublisherGroups.component.less');

angular.module('one.widgets').component('zemPublisherGroups', {
    template: require('./zemPublisherGroups.component.html'),
    bindings: {
        account: '<',
    },
    controller: function($filter, $uibModal, zemPublisherGroupsEndpoint) {
        var $ctrl = this;

        $ctrl.showCollapsed = false;
        $ctrl.loading = true;

        $ctrl.download = download;
        $ctrl.edit = edit;
        $ctrl.createNew = createNew;

        $ctrl.$onInit = function() {
            initPublisherGroups();
        };

        function initPublisherGroups() {
            zemPublisherGroupsEndpoint
                .list($ctrl.account.id)
                .then(function(data) {
                    $ctrl.publisherGroups = data;
                    $ctrl.loading = false;
                });
        }

        function download(publisherGroupId) {
            zemPublisherGroupsEndpoint.download(
                $ctrl.account.id,
                publisherGroupId
            );
        }

        function createNew() {
            openPublisherGroupModal(null);
        }

        function edit(publisherGroupId) {
            var publisherGroup = getPublisherGroup(publisherGroupId);

            if (publisherGroup) {
                openPublisherGroupModal(publisherGroup);
            }
        }

        function openPublisherGroupModal(publisherGroup) {
            var modal = $uibModal.open({
                component: 'zemPublisherGroupsUpload',
                backdrop: 'static',
                keyboard: false,
                windowClass: 'publisher-group-upload',
                resolve: {
                    publisherGroup: publisherGroup,
                    account: $ctrl.account,
                },
            });

            modal.result.then(initPublisherGroups);
        }

        function getPublisherGroup(publisherGroupId) {
            var publisherGroup = null;

            for (var i = 0; i < $ctrl.publisherGroups.length; i++) {
                if ($ctrl.publisherGroups[i].id === publisherGroupId) {
                    publisherGroup = $ctrl.publisherGroups[i];
                    break;
                }
            }

            return publisherGroup;
        }
    },
});
