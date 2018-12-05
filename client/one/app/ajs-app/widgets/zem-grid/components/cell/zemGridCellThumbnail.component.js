var creativesManagerHelpers = require('../../../../../features/creatives-manager/helpers/creatives-manager.helpers');
var creativesManagerConfig = require('../../../../../features/creatives-manager/creatives-manager.config')
    .CREATIVES_MANAGER_CONFIG;

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
        controller: function($sce) {
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

            vm.getIframeSrc = function(adTag) {
                var iframeSrc = creativesManagerHelpers.getPreviewIframeSrc(
                    creativesManagerConfig.previewIframeSrcPrefix,
                    adTag
                );
                // Use $sce (Strict Contextual Escaping) to render trusted values
                // https://docs.angularjs.org/api/ng/service/$sce
                return $sce.trustAsResourceUrl(iframeSrc);
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
