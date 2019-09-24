require('./zemReportColumnSelector.component.less');

angular.module('one.widgets').component('zemReportColumnSelector', {
    bindings: {
        disabled: '<',
        categories: '<',
        onColumnToggled: '&',
        onColumnsToggled: '&',
        onAllColumnsToggled: '&',
    },
    template: require('./zemReportColumnSelector.component.html'),
});
