/* global angular */

/**
 * Module used to inject all externall libraries' modules used by One app.
 */
angular.module(
    'one.libs',
    [
        'config',
        'templates-one',
        'ngSanitize',
        'ui.router',
        'ui.bootstrap',
        'ui.bootstrap.tooltip',
        'ui.bootstrap.datetimepicker',
        'daterangepicker',
        'ui.select',
        'ui.select2',
        'highcharts-ng',
    ]
);
