angular
    .module('one.widgets')
    .directive('zemGridModal', function(
        $rootScope,
        $timeout,
        $http,
        $templateCache,
        $compile,
        $document
    ) {
        // eslint-disable-line max-len
        var body;
        var pubsub;
        var deregisterLocationChangeStart;
        var deregisterVerticalScroll;
        var deregisterHorizontalScroll;
        var toggleElement;
        var relativePositionTop;
        var relativePositionLeft;
        var modal;

        function prepareModal(scope, element, attributes) {
            if (modal) {
                closeModal();
            }

            var modalTemplate = attributes.zemGridModal;
            if (!modalTemplate) {
                return;
            }

            toggleElement = element;
            relativePositionTop = parseInt(attributes.top) || 0;
            relativePositionLeft = parseInt(attributes.left) || 0;

            $http
                .get(modalTemplate, {cache: $templateCache})
                .success(function(template) {
                    compileModalTemplate(template, scope);
                });
        }

        function compileModalTemplate(template, scope) {
            // NOTE: Run in $timeout to allow ngUpgrade to register bindings in compiled template
            $timeout(function() {
                $compile(template)(scope, function(compiledModal) {
                    appendModalToGrid(compiledModal);
                });
            }, 0);
        }

        function appendModalToGrid(compiledModal) {
            var toggleElementPosition = toggleElement.offset();
            var modalCss = {
                top: toggleElementPosition.top + relativePositionTop + 'px',
                left: toggleElementPosition.left + relativePositionLeft + 'px',
            };
            toggleElement.addClass('modal-open');
            compiledModal.css(modalCss);
            body.append(compiledModal);
            modal = compiledModal;

            // Focus element with 'focus' attribute
            $timeout(function() {
                if (!modal) return;
                var inputToFocus = modal.find('[focus]');
                if (inputToFocus.length) {
                    inputToFocus[0].focus();
                }
            }, 0);

            // Listen for clicks outside modal and close the modal on click
            // NOTE: Event listener for clicks on modal is stopping event propagation so that modal is not closed if user
            // clicks on it
            body.on('click', closeModal);
            modal.on('click', function(event) {
                event.stopPropagation();
            });
            // Close modal when navigating to different route (e.g. using navigation search)
            deregisterLocationChangeStart = $rootScope.$on(
                '$locationChangeStart',
                closeModal
            );

            deregisterVerticalScroll = pubsub.register(
                pubsub.EVENTS.BODY_VERTICAL_SCROLL,
                null,
                closeModal
            );
            deregisterHorizontalScroll = pubsub.register(
                pubsub.EVENTS.BODY_HORIZONTAL_SCROLL,
                null,
                closeModal
            );
        }

        function closeModal() {
            if (modal) {
                modal.off('click');
                modal.remove();
                modal = null;
            }
            body.off('click');

            deregisterVerticalScroll();
            deregisterHorizontalScroll();
            deregisterLocationChangeStart();

            toggleElement.removeClass('modal-open');
        }

        return {
            restrict: 'A',
            scope: false,
            link: function(scope, element, attributes) {
                body = $document.find('body');
                pubsub = scope.ctrl.grid.meta.pubsub;

                element.on('click', function() {
                    if (modal) {
                        closeModal();
                    } else {
                        prepareModal(scope, element, attributes);
                    }
                });

                // Set simple api to interact with modal from directive on which zemGridModal was applied
                scope.ctrl.modal = {
                    close: closeModal,
                };
            },
            controller: function() {},
        };
    });
