import * as clone from 'clone';

export function getValueOrDefault<T>(value: T, defaultValue: T): T {
    if (isDefined(value)) {
        return clone(value);
    }
    return defaultValue;
}

export function isDefined(value: any): boolean {
    if (value === undefined || value === null) {
        return false;
    }
    return true;
}

export function insertStringAtIndex(
    currentValue: string,
    indexToInsert: number,
    valueToInsert: string
) {
    if (!isDefined(currentValue) || currentValue === '') {
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
