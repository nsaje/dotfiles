/* globals oneApp, options, defaults, constants, angular, $ */
'use strict';

oneApp.directive('zemUploadEditForm', [function () { // eslint-disable-line max-len
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        bindToController: {
            api: '=',
            endpoint: '=',
            callback: '=',
            batchId: '=',
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
        },
        controller: 'ZemUploadEditFormCtrl',
    };
}]);

oneApp.controller('ZemUploadEditFormCtrl', ['config', '$q', function (config, $q) {
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

    vm.api.requestInProgress = false;
    vm.api.selectedId = null;
    vm.api.open = function (candidate) {
        vm.api.requestInProgress = false;
        vm.requestFailed = false;
        vm.selectedCandidate = angular.copy(candidate);
        vm.selectedCandidate.defaults = {};
        vm.selectedCandidate.useTrackers = !!vm.selectedCandidate.primaryTrackerUrl ||
            !!vm.selectedCandidate.secondaryTrackerUrl;
        vm.selectedCandidate.useSecondaryTracker = !!vm.selectedCandidate.secondaryTrackerUrl;
        vm.scrollTop();
        vm.api.selectedId = candidate.id;
    };

    vm.api.close = function () {
        vm.api.selectedId = null;
        vm.selectedCandidate = null;
    };

    vm.api.update = function () {
        vm.scrollBottom();
        return vm.update();
    };

    vm.update = function () {
        vm.api.requestInProgress = true;
        vm.requestFailed = false;

        return vm.endpoint.updateCandidate(
            vm.selectedCandidate,
            vm.batchId
        ).then(function (result) {
            vm.callback(result.candidates);
            vm.api.close();
        }, function () {
            vm.requestFailed = true;
        }).finally(function () {
            vm.api.requestInProgress = false;
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
        if (!vm.selectedCandidate || !vm.selectedCandidate.errors) {
            return;
        }

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

    vm.close = function () {
        vm.closeModal();
    };
}]);
