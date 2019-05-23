var iframeHelpers = require('../../../../../shared/helpers/iframe.helpers');

angular.module('one.widgets').directive('zemGridCellThumbnail', function() {
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            data: '=',
            column: '=',
            row: '=',
            grid: '=',
        },
        template: require('./zemGridCellThumbnail.component.html'),
        controller: function() {
            var vm = this;

            vm.isNative = function() {
                return !vm.isImage() && !vm.isAdTag();
            };

            vm.isImage = function() {
                if (!vm.row.data.stats.creative_type.value) return false;
                var adType = options.adTypes.find(function(item) {
                    return item.name === vm.row.data.stats.creative_type.value;
                });
                return adType && adType.value === constants.adType.IMAGE;
            };

            vm.isAdTag = function() {
                if (!vm.row.data.stats.creative_type.value) return false;
                var adType = options.adTypes.find(function(item) {
                    return item.name === vm.row.data.stats.creative_type.value;
                });
                return adType && adType.value === constants.adType.AD_TAG;
            };

            vm.getCreativeWidth = function() {
                if (vm.row.data.stats.creative_size) {
                    var sizes = parseSize(
                        vm.row.data.stats.creative_size.value
                    );
                    return parseInt(sizes[0]);
                }
                return 300;
            };

            vm.getCreativeHeight = function() {
                if (vm.row.data.stats.creative_size) {
                    var sizes = parseSize(
                        vm.row.data.stats.creative_size.value
                    );
                    return parseInt(sizes[1]);
                }
                return 250;
            };

            vm.renderAdTagInIframe = function(adTag) {
                var iframe = document.getElementById('ad-preview__iframe');
                iframeHelpers.renderContentInIframe(iframe, adTag);
            };

            function parseSize(value) {
                var sizes = value.split('x').map(function(item) {
                    return item.trim();
                });
                return sizes;
            }
        },
    };
});
