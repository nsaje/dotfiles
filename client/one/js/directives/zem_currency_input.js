/*globals oneApp,$*/
'use strict';

oneApp.directive('zemCurrencyInput', function() {
    return {
        require: 'ngModel',
        restrict: 'A',
        link: function postLink(scope, element, attrs, controller) {
            var caretPos = 0;
            var previousValue;

            function getCaretPos(element) {
                var range;
                var re;
                var rc;

                if (element.selectionStart) {
                    return element.selectionStart;
                }

                if (document.selection) {
                    // Handle IE <= 8.
                    //element.focus breaks ie10, commented out for now.
                    //element.focus();

                    range = document.selection.createRange();
                    if (range === null) {
                        return 0;
                    }

                    re = element.createTextRange();
                    rc = re.duplicate();
                    re.moveToBookmark(range.getBookmark());
                    rc.setEndPoint('EndToStart', re);

                    return rc.text.length;
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

            element.keydown(function(e) {
                caretPos = getCaretPos(element[0]);
            });

            function formatThousands(money) {
                var result = '';
                var i = 0;
                var iter = 1;
                if (money) {
                    for (i = money.length-1; i >= 0; i--) {
                        result = money[i] + result;
                        if (i > 0 && i < money.length-1 && iter % 3 === 0) {
                            result = ',' + result;
                        }
                        iter++;
                    }
                }

                return result;
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
                
                value = value.toString();

                var parts = value.split('.');
                var money = parts[0];
                var cents = parts[1];

                var result = formatThousands(money);

                result = [result, cents].join('.');
                previousValue = result;
                return result;
            }

            function toDecimal(value) {
                var transformedValue;
                var parts;
                var caretExtraCount;
                var thousandsPart;

                if (!value) {
                    previousValue = '';
                    return '';
                }

                transformedValue = value.replace(/[^\d\.]+/g, '');
                parts = transformedValue.split('.');

                // If there are more than one dot, only take the last one into
                // account if it is set otherwise, use the second last (we take
                // advantage of the fact, that there can never be more than 2 dots
                // here).
                if (parts.length > 2) {
                    if (parts[parts.length - 1]) {
                        thousandsPart = parts.splice(0, parts.length-1).join('');
                    } else {
                        thousandsPart = parts.splice(0, parts.length-2).join('');
                    }
                    parts = [thousandsPart, parts[0]];
                }

                if (parts.length > 0) {
                    parts[0] = formatThousands(parts[0]);
                }

                if (parts.length > 1) {
                    if (parts[1].length > 2) {
                        parts[1] = parts[1].slice(0, 2);
                    }
                }

                transformedValue = parts.join('.');
                if (transformedValue !== value) {
                    element.val(transformedValue);

                    caretExtraCount = transformedValue.length - previousValue.length;

                    setCaretPos(element[0], caretPos + caretExtraCount);
                }
                previousValue = transformedValue;

                transformedValue = addCents(transformedValue);

                var result = transformedValue.replace(',', '');

                if (isNaN(result)) {
                    return '';
                }

                return result;
            }

            element.bind('blur', function(e) {
                var value = $(this).val();
                var transformedValue = addCents(value);
                if (transformedValue !== value) {
                    element.val(transformedValue);
                }
            });

            controller.$formatters.push(fromDecimal);
            controller.$parsers.push(toDecimal);
        }
    };
});
