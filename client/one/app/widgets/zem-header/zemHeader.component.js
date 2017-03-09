angular.module('one.widgets').component('zemHeader', {
    templateUrl: '/app/widgets/zem-header/zemHeader.component.html',
    controller: function ($window, config) {
        var $ctrl = this;
        $ctrl.config = config;

        $ctrl.$onInit = function () {
            angular.element($window).on('scroll', handleScroll);
        };

        $ctrl.$onDestroy = function () {
            angular.element($window).off('scroll', handleScroll);
        };

        var isHeaderFixed = false;
        function handleScroll (event) {
            var st = $(event.target).scrollTop();
            if (!isHeaderFixed && st > 50) {
                isHeaderFixed = true;
                $('body').addClass('fixed-header');
            } else if (isHeaderFixed && st <= 50) {
                isHeaderFixed = false;
                $('body').removeClass('fixed-header');
            }
        }
    },
});
