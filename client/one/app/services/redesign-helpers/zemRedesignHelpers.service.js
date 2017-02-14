// TODO: Temporary service used to handle redesing related permission. Remove once redesign is finished.
angular.module('one.services').service('zemRedesignHelpersService', function () {
    // TEMPORARY SOLUTION SHOULD BE REFACTORED
    $(window).scroll(function () {
        var st = $(this).scrollTop();
        // FIXED HEADER
        if (st > 50) {
            $('body').addClass('fixed-header');
        } else {
            $('body').removeClass('fixed-header');
        }
    });

    function zemantaSecret () {
        $('body').append('<div class="ee-wrapper"></div>');
        $('.ee-wrapper').append('<div class="ee-zemanta-logo"></div>');
        $('.ee-wrapper').append('<div class="ee-zemanta-square ee-zemanta-square-1"></div>');
        $('.ee-wrapper').append('<div class="ee-zemanta-square ee-zemanta-square-2"></div>');
        $('.ee-wrapper').append('<div class="ee-zemanta-square ee-zemanta-square-3"></div>');
        $('.ee-wrapper').append('<div class="ee-zemanta-close">Click anywhere to close</div>');

        var boxSize = 50,
            position = [],
            wrapper = $('.ee-wrapper'),
            x = Math.round(wrapper.width () / boxSize) +
            (wrapper.width () % boxSize ? 1 : 0),
            y = Math.round(wrapper.height () / boxSize) +
            (wrapper.height () % boxSize ? 1 : 0),
            html = '';

        for (var i = 0; i < x; i++) {
            for (var j = 0; j < y; j++) {
                position.push({
                    x: i * boxSize,
                    y: j * boxSize
                });
            }
        }

        function Shuffle (el) {
            for (var a, c, b = el.length; b; a = parseInt(Math.random () * b), c = el[--b], el[b] = el[a], el[a] = c);
            return el;
        }

        Shuffle(position);

        for (var k = 0; k < position.length; k++) {
            html += '<div class="ee-box" style="left: ' + position[k].x + 'px; top: ' + position[k].y + 'px"></div>';
        }

        wrapper.append(html);

        $('.ee-box').css({
            'width': boxSize,
            'height': boxSize
        });

        $('.ee-zemanta-square').css({
            'width': boxSize,
            'height': boxSize
        });

        $('.ee-box').hover(function () {
            $(this).fadeToggle(500);
        });

        $('.ee-box').each(function (index) {
            $(this).delay(5 * index).fadeIn(500);
        });

        $('.ee-zemanta-logo').delay(5 * x * y).fadeIn(10000);
        $('.ee-zemanta-square-1').delay(5 * x * y + 4000).fadeIn(5000);
        $('.ee-zemanta-square-2').delay(5 * x * y + 4500).fadeIn(5000);
        $('.ee-zemanta-square-3').delay(5 * x * y + 5000).fadeIn(5000);
        $('.ee-zemanta-close').delay(5 * x * y + 15000).fadeIn(1000);

        $('.ee-wrapper').click(function () {
            $(this).remove();
        });
    }

    $(document).ready(function () {
        $('body').append('<div class="ee-zemanta-dots"></div>');

        $('.ee-zemanta-dots').click(function () {
            zemantaSecret();
        });
    });
});
