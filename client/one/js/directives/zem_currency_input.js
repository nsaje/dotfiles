/*globals oneApp,$*/
'use strict';

oneApp.directive('zemCurrencyInput', ['$filter', function($filter) {
    return {
        require: 'ngModel',
        restrict: 'A',
        scope: {
            prefix: '@?',
            fractionSize: '@?',
            replaceTrailingZeros: '=?'
        },
        compile: function compile(tElem, tAttrs) {
            // add attributes if not present
            if (!tAttrs.prefix) {
                tAttrs.prefix = '';
            }
            if (!tAttrs.fractionSize) {
                tAttrs.fractionSize = '';
            }

            return function postLink(scope, element, attrs, controller) {
                var decimalRegex;

                // sets defaults
                if (!scope.prefix) {
                    scope.prefix = '';
                }
                if (!scope.fractionSize) {
                    scope.fractionSize = '2';
                }

                decimalRegex = new RegExp('\\.[0-9]{0,' + scope.fractionSize + '}');
                
                function getCaretPos(element) {
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

                function fromDecimal(value) {
                    var integerPart;
                    var decimalPart;
                    var result;

                    if (!value || isNaN(value)) {
                        return scope.prefix;
                    }

                    value = value.toString();
                    integerPart = value.split('.')[0];
                    decimalPart = decimalRegex.exec(value);

                    // format with commas
                    result = scope.prefix + integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
                    if (decimalPart) {
                        result += decimalPart;
                    }

                    return result;
                }

                function toDecimal(value) {
                    var integerPart;
                    var decimalPart;

                    // replace all except digits and decimal dots
                    value = value.replace(/[^\d\.]+/g, '');

                    integerPart = value.split('.')[0];

                    // replace leading zeros
                    integerPart = integerPart.replace(/^0+(?=\d)/, '');

                    decimalPart = decimalRegex.exec(value);

                    return integerPart + (decimalPart || '');
                }

                function formatValue(value) {
                    return $filter('decimalCurrency')(value, '', scope.fractionSize, scope.replaceTrailingZeros);
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
                    if ((value.replace(/,/g, '').length - scope.prefix.length) > decimalValue.length) {
                        caretPos--;
                    }

                    setCaretPos(element[0], caretPos);
                });

                element.bind('blur', function(e) {
                    var value = element.val();

                    value = toDecimal(value);
                    value = formatValue(value);

                    element.val(scope.prefix + value);
                });

                controller.$formatters.push(fromDecimal);
                controller.$formatters.push(formatValue);

                controller.$parsers.push(toDecimal);
            };
        }
    };
}]);
