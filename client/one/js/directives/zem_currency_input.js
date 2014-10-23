/*globals oneApp,$*/
'use strict';

oneApp.directive('zemCurrencyInput', function() {
    return {
        require: 'ngModel',
        restrict: 'A',
        scope: {
            model: '=ngModel'
        },
        link: function postLink(scope, element, attrs, controller) {
            function getCaretPos(element) {
                var range;
                var re;
                var rc;

                if (element.selectionStart) {
                    return element.selectionStart;
                }

                return 0;
            }

            function setCaretPos(elem, caretPos) {
                if(elem !== null) {
                    if(elem.createTextRange) {
                        var range = elem.createTextRange();
                        range.move('character', caretPos);
                        range.select();
                    }
                    else {
                        if(elem.selectionStart) {
                            elem.focus();
                            elem.setSelectionRange(caretPos, caretPos);
                        }
                        else {
                            elem.focus();
                        }
                    }
                }
            }

            function addCents(money) {
                var decimalIndex;
                if (money) {
                    decimalIndex = money.indexOf('.');
                    if (decimalIndex === -1) {
                        money += '.00';
                    } else if (decimalIndex === money.length - 1) {
                        money += '00';
                    } else if (decimalIndex === money.length - 2) {
                        money += '0';
                    } else if (decimalIndex === 0) {
                        money = '0' + money;
                    }
                }

                return money;
            }

            function fromDecimal(value) {
                if (!value || isNaN(value)) {
                    return '';
                }

                // format with commas
                return value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
            }

            function toDecimal(value) {
                var integerPart;
                var decimalPart;

                // replace all except digits and decimal dots
                value = value.replace(/[^\d\.]+/g, '');

                integerPart = value.split('.')[0]

                // replace leading zeros
                integerPart = integerPart.replace(/^0+(?=\d)/, '');

                decimalPart = /\.[0-9]{0,2}/.exec(value);

                return integerPart + (decimalPart || '');
            }

            function getCommaCount(value, caretPos) {
                var count = value.slice(0, caretPos).match(/,/g) || [];
                return count.length;
            }

            element.bind('input', function(e) {
                var value = element.val();
                var caretPos = getCaretPos(element[0]);
                var decimalValue = toDecimal(value);
                var formattedValue = fromDecimal(decimalValue);

                element.val(formattedValue);

                // set caret position
                caretPos += getCommaCount(formattedValue, caretPos) - getCommaCount(value, caretPos);

                // adjust caret position if unallowed char was typed
                if (value.replace(/,/g, '').length > decimalValue.length) {
                    caretPos--;
                }

                setCaretPos(element[0], caretPos);
            });

            element.bind('blur', function(e) {
                var value = element.val();
                element.val(addCents(value));
            });

            controller.$formatters.push(fromDecimal);
            controller.$parsers.push(toDecimal);
        }
    };
});
