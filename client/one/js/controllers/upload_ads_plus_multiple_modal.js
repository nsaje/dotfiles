/* globals $, oneApp, options, defaults */
oneApp.controller('UploadAdsPlusMultipleModalCtrl', ['$scope',  '$modalInstance', function ($scope, $modalInstance) { // eslint-disable-line max-len
    $scope.imageCrops = options.imageCrops;

    $scope.partials = [
        '/partials/upload_ads_plus_multiple_modal_step1.html',
        '/partials/upload_ads_plus_multiple_modal_step2.html',
        '/partials/upload_ads_plus_multiple_modal_step3.html',
    ];
    $scope.step = 1;
    $scope.selectedCandidate = null;

    $scope.callToActionSelect2Config = {
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

    $scope.batchName = '5/22/2016 3:27 AM';
    $scope.candidates = [
        {
            id: 1,
            title: 'Title of content ad',
            status: 3,
            imageCrop: 'center',
            errors: [
                {
                    type: 'font',
                    text: 'Title too long',
                },
                {
                    type: 'picture',
                    text: 'Image too small',
                },
            ],
            callToAction: 'Read More',
        },
        {
            id: 2,
            title: 'Title of content ad that is longer and goes into more lines',
            status: 3,
            imageUrl: 'https://images2.zemanta.com/p/srv/8482/53d9f2fadc57444db3f2f549f3fa8786.jpg' +
                '?w=160&h=160&fit=crop&crop=faces&fm=jpg',
            errors: [
                {
                    type: 'font',
                    text: 'Title too long',
                },
            ],
        },
        {
            id: 3,
            title: 'Title of content ad',
            status: 2,
            imageUrl: 'https://images2.zemanta.com/p/srv/8482/53d9f2fadc57444db3f2f549f3fa8786.jpg' +
                '?w=160&h=160&fit=crop&crop=faces&fm=jpg',
        },
        {
            id: 4,
            title: 'Title of content ad',
            status: 2,
            imageUrl: 'https://images2.zemanta.com/p/srv/8482/53d9f2fadc57444db3f2f549f3fa8786.jpg' +
                '?w=160&h=160&fit=crop&crop=faces&fm=jpg',
        },
        {
            id: 5,
            title: 'Title of content ad',
            status: 1,
        },
    ];

    $scope.colorMap = {
        1: 'blue',
        2: 'green',
        3: 'red',
    };

    $scope.nextStep = function () {
        $scope.step++;
    };

    $scope.restart = function () {
        $scope.step = 1;
    };

    $scope.close = function () {
        $modalInstance.close();
    };

    $scope.openEditForm = function (candidate) {
        $scope.selectedCandidate = candidate;
    };

    $scope.closeEditForm = function () {
        $scope.selectedCandidate = null;
    };

    $scope.removeCandidate = function (candidate) {
        $scope.candidates = $scope.candidates.filter(function (el) {
            return candidate.id !== el.id;
        });

        if ($scope.selectedCandidate.id === candidate.id) {
            $scope.selectedCandidate = null;
        }
    };
}]);
