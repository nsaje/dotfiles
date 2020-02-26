var filter = require('rxjs/operators').filter;
var NavigationStart = require('@angular/router').NavigationStart;
var NavigationEnd = require('@angular/router').NavigationEnd;

angular.module('one', [
    'one.libs', // NOTE: Must be referenced first!
    'one.core',
    'one.common',
    'one.services',
    'one.widgets',
    'one.downgraded',
]);

angular.module('one.downgraded', []);

angular.module('one').config(function($compileProvider, config) {
    $compileProvider.debugInfoEnabled(
        config.env.dev || config.env.test || config.env.e2e
    );
});

angular.module('one').config(function($sceDelegateProvider, config) {
    $sceDelegateProvider.resourceUrlWhitelist([
        'self',
        config.staticUrl + '/**',
    ]);
});

angular.module('one').config(function($httpProvider) {
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
});

angular.module('one').config(function($locationProvider, config) {
    $locationProvider.html5Mode({
        enabled: true,
        requireBase: config.env.dev || config.env.prod || config.env.e2e,
    });
    $locationProvider.hashPrefix('!');
});

angular
    .module('one')
    .config(function(uibDatepickerConfig, uibDatepickerPopupConfig) {
        // eslint-disable-line max-len
        uibDatepickerConfig.showWeeks = false;
        uibDatepickerConfig.formatDayHeader = 'EEE';
        uibDatepickerPopupConfig.showButtonBar = false;
    });

angular.module('one').config(function($uibTooltipProvider) {
    $uibTooltipProvider.setTriggers({openTutorial: 'closeTutorial'});
});

// HACK: Update ui-select2 directive priority after initialization. There's a bug in deprecated angular-ui-select2
// library caused by library's incompatibility with Angular >= 1.5 that prevents ng-model changes to be reflected in
// ui-select2 directive.
angular.module('one').config(function($provide) {
    $provide.decorator('uiSelect2Directive', function($delegate) {
        var directive = $delegate[0];
        directive.priority = 10;
        return $delegate;
    });
});

// HACK: Decorate uib-dropdown-toggle to add/remove no-scroll--mobile class to/from body in order to prevent  scrolling
// of the page when dropdowns are open on mobile devices.
angular.module('one').config(function($provide) {
    $provide.decorator('uibDropdownToggleDirective', function($delegate) {
        var directive = $delegate[0];
        var originalLinkFn = directive.link;
        directive.compile = function() {
            return function newLinkFn(scope, element, attrs, dropdownCtrl) {
                originalLinkFn.apply(directive, arguments);
                scope.$watch(dropdownCtrl.isOpen, function(isDropdownOpen) {
                    if (!element.hasClass('dropdown-toggle--no-mobile-style')) {
                        if (isDropdownOpen) {
                            $('body').addClass('no-scroll--mobile');
                        } else {
                            $('body').removeClass('no-scroll--mobile');
                        }
                    }
                });
            };
        };
        return $delegate;
    });
});

angular
    .module('one')
    .run(function(NgRouter, $rootScope, config, zemIntercomService) {
        // eslint-disable-line max-len
        $rootScope.config = config;

        NgRouter.events
            .pipe(
                filter(function(event) {
                    return event instanceof NavigationStart;
                })
            )
            .subscribe(function() {
                $rootScope.$broadcast('$zemNavigationStart');
            });
        NgRouter.events
            .pipe(
                filter(function(event) {
                    return event instanceof NavigationEnd;
                })
            )
            .subscribe(function() {
                zemIntercomService.update();
                $rootScope.$broadcast('$zemNavigationEnd');
            });
    });

angular.module('one').config(function($provide) {
    // Fix sourcemaps
    // @url https://github.com/angular/angular.js/issues/5217#issuecomment-50993513
    $provide.decorator('$exceptionHandler', function() {
        return function(exception) {
            setTimeout(function() {
                throw exception;
            });
        };
    });
});

(function() {
    var downgradeInjectable = require('@angular/upgrade/static')
        .downgradeInjectable;

    var NgZone = require('@angular/core').NgZone;
    angular
        .module('one.downgraded')
        .factory('NgZone', downgradeInjectable(NgZone));

    var NgRouter = require('@angular/router').Router;
    angular
        .module('one.downgraded')
        .factory('NgRouter', downgradeInjectable(NgRouter));
})();
