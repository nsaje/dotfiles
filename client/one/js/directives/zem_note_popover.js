/*global $,oneApp*/
"use strict";

oneApp.directive('zemNotePopover', ['$window', function($window) {
    return {
        restrict: 'E',
        scope: {
            content: '@',
            placement: '@'
        },
        link: function(scope, element, attrs) {
            function attachment (url, fileExt) {
                var parts;
                if (!fileExt) {
                    parts = url.split('.');
                    fileExt = parts[parts.length -1 ];
                }
                return ' <i class="glyphicon glyphicon-paperclip"></i>' + fileExt;
            }
            function link (name) {
                return ' <i class="glyphicon glyphicon-link"></i>' + name.replace('www.', '');
            }
            scope.parsedContent = scope.content.replace(/https?:\/\/[^ ]*/g, function (match) {
                var a = $window.document.createElement('a');
                a.href = match;
                if (a.hostname.match(/trello-attachments\.s3\.amazonaws.com/) !== null) {
                    
                    return '<a target="_blank" href="' + match + '">' + attachment(match) + '</a>';
                }
                return '<a target="_blank" href="' + match + '">' + link(a.hostname) + '</a>';
            });
        },
        template: '<i ng-if="!!content" class="glyphicon glyphicon-align-justify" zem-lazy-popover-html-unsafe="{{ parsedContent }}" zem-lazy-popover-event="click" zem-lazy-popover-placement="{{ placement }}" zem-lazy-popover-append-to-body="true" zem-lazy-popover-animation-class="fade"></i><span ng-if="!content">N/A</span>'
    };
}]);
