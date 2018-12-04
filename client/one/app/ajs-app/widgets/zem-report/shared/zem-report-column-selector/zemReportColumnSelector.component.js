require('./zemReportColumnSelector.component.less');

angular.module('one.widgets').component('zemReportColumnSelector', {
    bindings: {
        disabled: '<',
        categories: '<',
        onColumnToggled: '&',
        onAllColumnsToggled: '&',
    },
    template: require('./zemReportColumnSelector.component.html'),
});
