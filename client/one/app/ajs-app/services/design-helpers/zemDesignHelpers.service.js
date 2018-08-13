angular.module('one.services').service('zemDesignHelpersService', function() {
    this.init = init;

    function init() {
        $('body').append(
            '<div class="ee-zemanta-dots"></div><a href="javascript:void(0)" class="scroll-to-top"></a>'
        );
        $(document).ready(function() {
            initScrollToTop();
            initZemantaSecret();
        });
    }

    function initScrollToTop() {
        $(window).scroll(function() {
            if ($(this).scrollTop() >= 600) {
                $('.scroll-to-top').addClass('scroll-to-top--visible');
            } else {
                $('.scroll-to-top').removeClass('scroll-to-top--visible');
            }
        });

        $('.scroll-to-top').click(function() {
            $('html, body').animate({scrollTop: 0}, 500);
        });
    }

    function initZemantaSecret() {
        $('.ee-zemanta-dots').click(function() {
            zemantaSecret();
        });
    }

    function zemantaSecret() {
        $('body').append('<div class="ee-wrapper"></div>');
        $('.ee-wrapper').append('<div class="ee-zemanta-logo"></div>');
        $('.ee-wrapper').append(
            '<div class="ee-zemanta-square ee-zemanta-square-1"></div>'
        );
        $('.ee-wrapper').append(
            '<div class="ee-zemanta-square ee-zemanta-square-2"></div>'
        );
        $('.ee-wrapper').append(
            '<div class="ee-zemanta-square ee-zemanta-square-3"></div>'
        );
        $('.ee-wrapper').append(
            '<div class="ee-zemanta-close">Click anywhere to close</div>'
        );

        var boxSize = 50,
            position = [],
            wrapper = $('.ee-wrapper'),
            x =
                Math.round(wrapper.width() / boxSize) +
                (wrapper.width() % boxSize ? 1 : 0),
            y =
                Math.round(wrapper.height() / boxSize) +
                (wrapper.height() % boxSize ? 1 : 0),
            html = '';

        for (var i = 0; i < x; i++) {
            for (var j = 0; j < y; j++) {
                position.push({
                    x: i * boxSize,
                    y: j * boxSize,
                });
            }
        }

        function Shuffle(el) {
            for (
                var a, c, b = el.length;
                b;
                a = parseInt(Math.random() * b),
                    c = el[--b],
                    el[b] = el[a],
                    el[a] = c
            );
            return el;
        }

        Shuffle(position);

        for (var k = 0; k < position.length; k++) {
            html +=
                '<div class="ee-box" style="left: ' +
                position[k].x +
                'px; top: ' +
                position[k].y +
                'px"></div>';
        }

        wrapper.append(html);

        $('.ee-box').css({
            width: boxSize,
            height: boxSize,
        });

        $('.ee-zemanta-square').css({
            width: boxSize,
            height: boxSize,
        });

        $('.ee-box').hover(function() {
            $(this).fadeToggle(500);
        });

        $('.ee-box').each(function(index) {
            $(this)
                .delay(5 * index)
                .fadeIn(500);
        });

        $('.ee-zemanta-logo')
            .delay(5 * x * y)
            .fadeIn(10000);
        $('.ee-zemanta-square-1')
            .delay(5 * x * y + 4000)
            .fadeIn(5000);
        $('.ee-zemanta-square-2')
            .delay(5 * x * y + 4500)
            .fadeIn(5000);
        $('.ee-zemanta-square-3')
            .delay(5 * x * y + 5000)
            .fadeIn(5000);
        $('.ee-zemanta-close')
            .delay(5 * x * y + 15000)
            .fadeIn(1000);

        $('.ee-wrapper').click(function() {
            $(this).remove();
        });
    }
});
