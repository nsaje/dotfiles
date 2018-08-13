angular
    .module('one.widgets')
    .service('zemHeaderNavigationService', function(zemNavigationNewService) {
        // eslint-disable-line max-len
        this.quickNavigate = quickNavigate;

        function quickNavigate(event) {
            var entity = zemNavigationNewService.getActiveEntity();
            if (!entity) {
                var firstAccount = zemNavigationNewService.getNavigationHierarchy()
                    .children[0];
                zemNavigationNewService.navigateTo(firstAccount);
                return;
            }

            var parent = entity.parent
                ? entity.parent
                : zemNavigationNewService.getNavigationHierarchy();
            var entityIdx = parent.children.indexOf(entity);

            var navigateToEntity = undefined;

            switch (event.key) {
                case 'ArrowUp':
                    var nextEntityIdx =
                        (entityIdx + 1) % parent.children.length;
                    navigateToEntity = parent.children[nextEntityIdx];
                    break;
                case 'ArrowDown':
                    var previousEntityIdx =
                        (entityIdx - 1 + parent.children.length) %
                        parent.children.length;
                    navigateToEntity = parent.children[previousEntityIdx];
                    break;
                case 'ArrowLeft':
                    navigateToEntity = parent;
                    break;
                case 'ArrowRight':
                    navigateToEntity = entity.children
                        ? entity.children[0]
                        : undefined;
                    break;
            }

            if (navigateToEntity !== undefined) {
                zemNavigationNewService.navigateTo(navigateToEntity);
            }
        }
    });
