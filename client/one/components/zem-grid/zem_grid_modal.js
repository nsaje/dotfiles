/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridModal', ['$http', '$templateCache', '$compile', '$document', function ($http, $templateCache, $compile, $document) { // eslint-disable-line max-len
    var body;
    var pubsub;
    var deregisterVerticalScroll;
    var deregisterHorizontalScroll;
    var toggleElement;
    var modalTemplate;
    var relativePositionTop;
    var relativePositionLeft;
    var modal;

    function prepareModal (element, scope) {
        if (!modalTemplate) {
            return;
        }

        if (modal) {
            closeModal();
        }

        toggleElement = angular.element(element);

        $http.get(modalTemplate, {cache: $templateCache}).success(function (template) {
            compileModalTemplate(template, scope);
        });
    }

    function compileModalTemplate (template, scope) {
        $compile(template)(scope, function (compiledModal) {
            appendModalToGrid(compiledModal);
        });
    }

    function appendModalToGrid (compiledModal) {
        var toggleElementPosition = toggleElement.offset();
        var modalCss = {
            top: (toggleElementPosition.top + relativePositionTop) + 'px',
            left: (toggleElementPosition.left + relativePositionLeft) + 'px',
        };
        toggleElement.addClass('modal-open');
        compiledModal.css(modalCss);
        body.append(compiledModal);
        modal = compiledModal;

        // Listen for clicks outside modal and close the modal on click
        // NOTE: Event listener for clicks on modal is stopping event propagation so that modal is not closed if user
        // clicks on it
        body.on('click', function () {
            closeModal();
        });
        modal.on('click', function (event) {
            event.stopPropagation();
        });

        deregisterVerticalScroll = pubsub.register(pubsub.EVENTS.BODY_VERTICAL_SCROLL, closeModal);
        deregisterHorizontalScroll = pubsub.register(pubsub.EVENTS.BODY_HORIZONTAL_SCROLL, closeModal);
    }

    function closeModal () {
        if (modal) {
            modal.off('click');
            modal.remove();
            modal = null;
        }
        body.off('click');
        deregisterVerticalScroll();
        deregisterHorizontalScroll();
        toggleElement.removeClass('modal-open');
    }

    return {
        restrict: 'A',
        scope: false,
        link: function (scope, element, attributes) {
            body = $document.find('body');
            pubsub = scope.ctrl.grid.meta.pubsub;
            modalTemplate = attributes.zemGridModal;
            relativePositionTop = parseInt(attributes.top) || 0;
            relativePositionLeft = parseInt(attributes.left) || 0;

            element.on('click', function () {
                if (modal) {
                    closeModal();
                } else {
                    prepareModal(this, scope);
                }
            });

            // Set simple api to interact with modal from directive on which zemGridModal was applied
            scope.ctrl.modal = {
                close: closeModal,
            };
        },
        controller: [function () {}],
    };
}]);
