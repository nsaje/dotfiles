import * as commonHelpers from './common.helpers';

export function insertStringAtIndex(
    currentValue: string,
    indexToInsert: number,
    valueToInsert: string
) {
    if (!commonHelpers.isDefined(currentValue) || currentValue === '') {
        return valueToInsert;
    }
    if (indexToInsert > 0) {
        return (
            currentValue.substring(0, indexToInsert) +
            valueToInsert +
            currentValue.substring(indexToInsert, currentValue.length)
        );
    }
    return valueToInsert + currentValue;
}
