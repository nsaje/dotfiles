require('./zemPublisherGroups.component.less');

var commonHelpers = require('../../../shared/helpers/common.helpers');

angular.module('one.widgets').component('zemPublisherGroups', {
    template: require('./zemPublisherGroups.component.html'),
    bindings: {
        account: '<',
        agency: '<',
    },
    controller: function(
        $filter,
        $uibModal,
        zemPublisherGroupsEndpoint,
        zemPermissions
    ) {
        var $ctrl = this;
        var hasAgencyScope = false;

        $ctrl.showCollapsed = false;
        $ctrl.loading = true;

        $ctrl.download = download;
        $ctrl.openPublisherGroupModal = openPublisherGroupModal;
        $ctrl.isReadOnly = isReadOnly;
        $ctrl.createNew = createNew;

        $ctrl.$onInit = function() {
            initPublisherGroups();

            if (commonHelpers.isDefined($ctrl.agency)) {
                hasAgencyScope = zemPermissions.hasAgencyScope($ctrl.agency.id);
            }
        };

        function getAccountId() {
            if (commonHelpers.isDefined($ctrl.account)) {
                return $ctrl.account.id;
            }
            return null;
        }

        function getAgencyId() {
            if (commonHelpers.isDefined($ctrl.agency)) {
                return $ctrl.agency.id;
            }
            return null;
        }

        function initPublisherGroups() {
            zemPublisherGroupsEndpoint
                .list(getAccountId(), getAgencyId())
                .then(function(data) {
                    $ctrl.publisherGroups = data;
                    $ctrl.loading = false;
                    $ctrl.publisherGroups.forEach(function(pg) {
                        pg.isReadOnly = isReadOnly(pg);
                    });
                });
        }

        function download(publisherGroupId) {
            zemPublisherGroupsEndpoint.download(
                getAccountId(),
                getAgencyId(),
                publisherGroupId
            );
        }

        function createNew() {
            openPublisherGroupModal(null);
        }

        function isReadOnly(publisherGroup) {
            if (publisherGroup.agency_id && !hasAgencyScope) {
                return true;
            }
            return false;
        }

        function openPublisherGroupModal(publisherGroup) {
            var isNew = !commonHelpers.isDefined(publisherGroup);
            var modal = $uibModal.open({
                component: 'zemPublisherGroupsUpload',
                backdrop: 'static',
                keyboard: false,
                windowClass: 'publisher-group-upload',
                resolve: {
                    publisherGroup: publisherGroup,
                    account: $ctrl.account,
                    agency: $ctrl.agency,
                    isReadOnly: !isNew && publisherGroup.isReadOnly,
                },
            });

            modal.result.then(initPublisherGroups);
        }
    },
});
