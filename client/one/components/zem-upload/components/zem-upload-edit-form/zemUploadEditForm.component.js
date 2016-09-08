/* globals options, defaults, constants, angular, $ */
'use strict';

angular.module('one.legacy').directive('zemUploadEditForm', [function () { // eslint-disable-line max-len
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        bindToController: {
            api: '=',
            endpoint: '=',
            callback: '=',
            batchId: '=',
            hasPermission: '=',
        },
        controllerAs: 'ctrl',
        templateUrl: '/components/zem-upload/components/zem-upload-edit-form/zemUploadEditForm.component.html',
        link: function (scope, element, attrs, ctrl) {
            ctrl.scrollTop = function () {
                element[0].scrollTop = 0;
            };
            ctrl.scrollBottom = function () {
                element[0].scrollTop = element[0].scrollHeight;
            };

            var callToActionInput = element.find('#call-to-action-input');
            callToActionInput.on('select2-opening', function () {
                // workaround for select 2 that doesn't broadcast ng-click very well
                ctrl.clearSelectedCandidateErrors('callToAction');
            });
        },
        controller: 'ZemUploadEditFormCtrl',
    };
}]);

angular.module('one.legacy').controller('ZemUploadEditFormCtrl', ['config', '$q', function (config, $q) {
    var vm = this;
    vm.config = config;

    vm.MAX_URL_LENGTH = 936;
    vm.MAX_TITLE_LENGTH = 90;
    vm.MAX_DESCRIPTION_LENGTH = 140;
    vm.MAX_DISPLAY_URL_LENGTH = 25;
    vm.MAX_BRAND_NAME_LENGTH = 25;
    vm.MAX_CALL_TO_ACTION_LENGTH = 25;
    vm.MAX_LABEL_LENGTH = 100;

    vm.imageCrops = options.imageCrops;
    vm.callToActionOptions = defaults.callToAction;
    vm.candidateStatuses = constants.contentAdCandidateStatus;

    // content ad picker API
    vm.api.requestInProgress = false;
    vm.api.selectedId = null;
    vm.api.open = open;
    vm.api.close = refreshAndClose;
    vm.api.update = scrollBottomAndUpdate;

    function open (candidate) {
        vm.api.requestInProgress = false;
        vm.requestFailed = false;
        vm.selectedCandidate = candidate;
        if (!vm.hasPermission('zemauth.can_use_partial_updates_in_upload')) {
            vm.selectedCandidate = angular.copy(vm.selectedCandidate);
        }
        vm.selectedCandidate.defaults = {};
        vm.selectedCandidate.useTrackers = !!vm.selectedCandidate.primaryTrackerUrl ||
            !!vm.selectedCandidate.secondaryTrackerUrl;
        vm.selectedCandidate.useSecondaryTracker = !!vm.selectedCandidate.secondaryTrackerUrl;
        vm.scrollTop();
        vm.api.selectedId = candidate.id;
    }

    function scrollBottomAndUpdate () {
        vm.scrollBottom();
        return vm.update();
    }

    function refreshAndClose () {
        close();
        vm.endpoint.getCandidates(vm.batchId).then(function (result) {
            vm.callback(result.candidates);
        });
    }

    function close () {
        vm.api.selectedId = null;
        vm.selectedCandidate = null;
    }

    vm.update = function () {
        vm.api.requestInProgress = true;
        vm.requestFailed = false;

        return vm.endpoint.updateCandidate(
            vm.selectedCandidate,
            vm.batchId
        ).then(function (result) {
            vm.callback(result.candidates);
            close();
        }, function () {
            vm.requestFailed = true;
        }).finally(function () {
            vm.api.requestInProgress = false;
        });
    };

    vm.updateField = function (field) {
        if (!vm.hasPermission('zemauth.can_use_partial_updates_in_upload')) return;

        var data = {
            id: vm.selectedCandidate.id,
        };
        data[field] = vm.selectedCandidate[field];

        vm.endpoint.updateCandidatePartial(vm.batchId, data).then(function (data) {
            if (!data.errors.hasOwnProperty(field)) {
                delete vm.selectedCandidate.errors[field];
                return;
            }

            vm.selectedCandidate.errors[field] = data.errors[field];
        });
    };

    vm.addSecondaryTracker = function (candidate) {
        candidate.useSecondaryTracker = true;
    };

    vm.removeSecondaryTracker = function (candidate) {
        candidate.useSecondaryTracker = false;
        candidate.secondaryTrackerUrl = null;
        vm.clearSelectedCandidateErrors('secondaryTrackerUrl');
    };

    vm.clearSelectedCandidateErrors = function (field) {
        if (!vm.selectedCandidate || !vm.selectedCandidate.errors) return;
        if (vm.hasPermission('zemauth.can_use_partial_updates_in_upload')) return;

        delete vm.selectedCandidate.errors[field];
    };

    vm.callToActionSelect2Config = {
        dropdownCssClass: 'service-fee-select2',
        createSearchChoice: function (term, data) {
            if ($(data).filter(function () {
                return this.text.localeCompare(term) === 0;
            }).length === 0) {
                return {id: term, text: term};
            }
        },
        data: defaults.callToAction,
    };
}]);
