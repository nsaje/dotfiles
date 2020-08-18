require('./zemCloneContentModal.component.less');

angular.module('one.widgets').component('zemCloneContentModal', {
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    template: require('./zemCloneContentModal.component.html'),
    controller: function(
        $q,
        zemAuthStore,
        zemNavigationNewService,
        zemCloneContentService,
        zemSelectDataStore
    ) {
        //eslint-disable-line max-len
        var $ctrl = this;
        $ctrl.texts = {
            placeholder: 'Search ad group ...',
        };

        //
        // Public
        //
        $ctrl.submit = submit;
        $ctrl.onAdGroupSelected = onAdGroupSelected;

        //
        // Private
        //
        $ctrl.adGroup = null;
        $ctrl.destinationAdGroupId = null;
        $ctrl.destinationBatchName = null;
        $ctrl.clonedContentState = null;

        $ctrl.errors = null;
        $ctrl.requestInProgress = false;

        $ctrl.$onInit = function() {
            var promise = zemNavigationNewService
                .getNavigationHierarchyPromise()
                .then(function() {
                    return zemNavigationNewService.getEntityById(
                        constants.entityType.AD_GROUP,
                        $ctrl.resolve.adGroupId
                    );
                })
                .then(function(adGroup) {
                    $ctrl.adGroup = adGroup;
                    var user = zemAuthStore.getCurrentUser(),
                        time = moment()
                            .utc()
                            .add(user ? user.timezoneOffset : 0, 'seconds')
                            .format('M/D/YYYY h:mm A');

                    $ctrl.destinationBatchName =
                        'Cloned from ' + $ctrl.adGroup.name + ' on ' + time;

                    return getDataStoreItems();
                });
            $ctrl.store = zemSelectDataStore.createInstance(promise);
        };

        function submit() {
            $ctrl.requestInProgress = true;

            zemCloneContentService
                .clone({
                    adGroupId: $ctrl.resolve.adGroupId,
                    selection: $ctrl.resolve.selection,
                    destinationAdGroupId: $ctrl.destinationAdGroupId,
                    destinationBatchName: $ctrl.destinationBatchName,
                    state: $ctrl.clonedContentState,
                })
                .then(
                    function(data) {
                        $ctrl.modalInstance.close(data);
                    },
                    function(errors) {
                        $ctrl.errors = errors;
                    }
                )
                .finally(function() {
                    $ctrl.requestInProgress = false;
                });
        }

        // zem UI select properties
        //
        function getDataStoreItems() {
            var item,
                adGroups = [];
            angular.forEach(
                zemNavigationNewService.getNavigationHierarchy().ids.adGroups,
                function(value) {
                    if (!value.data.archived) {
                        item = {
                            id: value.id,
                            name: value.name,
                            h1: value.parent.parent.name,
                            h2: value.parent.name,
                            searchableName:
                                value.parent.parent.name +
                                ' ' +
                                value.parent.name +
                                ' ' +
                                value.name,
                        };
                        if (
                            value.parent.parent.id ===
                            $ctrl.adGroup.parent.parent.id
                        ) {
                            adGroups.push(item);
                        }
                    }
                }
            );
            return adGroups;
        }

        function onAdGroupSelected(item) {
            $ctrl.destinationAdGroupId = item ? item.id : null;
        }
    },
});
