/*globals oneApp*/
'use strict';

oneApp.directive('zemCurrencyInput', function() {
    return {
        require: 'ngModel',
        restrict: 'A',
        link: function postLink(scope, element, attrs, controller) {
            var caretPos = 0;

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
                return result;
            }

            function toDecimal(value) {
                var transformedValue;
                var parts;
                var caretExtraCount;

                if (!value) {
                    return '';
                }

                transformedValue = value.replace(/[^\d\.]+/g, '');
                parts = transformedValue.split('.');

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
                    controller.$setViewValue(transformedValue);
                    controller.$render();

                    caretExtraCount = transformedValue.length - value.length;
                    // TODO: Fix backspace deletion.
                    if (caretExtraCount >= 0) {
                        caretExtraCount += 1;
                    } else {
                        caretExtraCount -= 1;
                    }

                    setCaretPos(element[0], caretPos + caretExtraCount);
                }

                transformedValue = addCents(transformedValue);

                var result = transformedValue.replace(',', '');

                if (isNaN(result)) {
                    return '';
                }

                return result;
            }

            element.bind('blur', function() {
                var value = controller.$viewValue;
                var transformedValue = addCents(value);
                if (transformedValue !== value) {
                    controller.$setViewValue(transformedValue);
                    controller.$render();
                }
            });

            controller.$formatters.push(fromDecimal);
            controller.$parsers.push(toDecimal);
        }
    };
});
