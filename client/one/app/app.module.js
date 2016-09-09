angular.module(
    'one',
    [
        'one.libs', // NOTE: Must be referenced first!
        'one.core',
        'one.common',
        'one.services',
        'one.views',
        'one.widgets',
        'one.legacy',
    ]
);

angular.module('one').config(['$compileProvider', 'config', function ($compileProvider, config) {
    $compileProvider.debugInfoEnabled(config.debug);
}]);

angular.module('one').config(['$sceDelegateProvider', 'config', function ($sceDelegateProvider, config) {
    $sceDelegateProvider.resourceUrlWhitelist(['self', config.static_url + '/**']);
}]);

angular.module('one').config(['$httpProvider', function ($httpProvider) {
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
}]);

angular.module('one').config(['$locationProvider', function ($locationProvider) {
    $locationProvider.html5Mode(true);
    $locationProvider.hashPrefix('!');
}]);

angular.module('one').config(['uibDatepickerConfig', 'uibDatepickerPopupConfig', function (datepickerConfig, datepickerPopupConfig) { // eslint-disable-line max-len
    datepickerConfig.showWeeks = false;
    datepickerConfig.formatDayHeader = 'EEE';
    datepickerPopupConfig.showButtonBar = false;
}]);

angular.module('one').config(['$uibTooltipProvider', function ($tooltipProvider) {
    $tooltipProvider.setTriggers({'openTutorial': 'closeTutorial'});
}]);

// HACK: Update ui-select2 directive priority after initialization. There's a bug in deprecated angular-ui-select2
// library caused by library's incompatibility with Angular >= 1.5 that prevents ng-model changes to be reflected in
// ui-select2 directive.
angular.module('one').config(['$provide', function ($provide) {
    $provide.decorator('uiSelect2Directive', ['$delegate', function ($delegate) {
        var directive;
        directive = $delegate[0];
        directive.priority = 10;
        return $delegate;
    }]);
}]);

var locationSearch;
// Fixes https://github.com/angular-ui/ui-router/issues/679
angular.module('one').run(['$state', '$rootScope', '$location', 'config', 'zemIntercomService', function ($state, $rootScope, $location, config, zemIntercomService) {  // eslint-disable-line max-len
    $rootScope.config = config;
    $rootScope.$state = $state;

    $rootScope.$on('$stateChangeStart', function () {
        // Save location.search so we can add it back after transition is done
        locationSearch = $location.search();
    });

    $rootScope.$on('$stateChangeSuccess', function () {
        // Restore all query string parameters back to $location.search
        $location.search(locationSearch);
        $rootScope.stateChangeFired = true;
    });

    $rootScope.$on('$locationChangeSuccess', function () {
        zemIntercomService.update();
    });

    $rootScope.tabClick = function (event) {
        // Function to fix opening tabs in new tab when clicking with the middle button
        // This is effectively a workaround for a bug in bootstrap-ui
        if (event.which === 2 || (event.which === 1 && (event.metaKey || event.ctrlKey))) {
           // MIDDLE CLICK or CMD+LEFTCLICK
           // the regular link will open in new tab if we stop the event propagation
            event.stopPropagation();
        }
    };
}]);
