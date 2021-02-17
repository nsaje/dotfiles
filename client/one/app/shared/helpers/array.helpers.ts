import * as commonHelpers from './common.helpers';
import * as deepEqual from 'fast-deep-equal';

export function isEmpty(value: any[]): boolean {
    if (!commonHelpers.isDefined(value)) {
        return true;
    }
    return value.length === 0;
}

export function intersect<T>(array1: T[], array2: T[]) {
    if (isEmpty(array1) || isEmpty(array2)) {
        return [];
    } else {
        if (commonHelpers.isPrimitive(array1[0])) {
            // Do a fast and simple check for primitive types
            // Return elements of array array1 that are also in array2 in linear time
            return array1.filter(Set.prototype.has, new Set(array2));
        } else {
            // Call a function that uses deep-equal to check complex types
            return array1.filter(v1 =>
                commonHelpers.isEqualToAnyItem(v1, array2)
            );
        }
    }
}

export function includesAny<T>(array1: T[], array2: T[]) {
    return intersect(array1, array2).length > 0;
}

export function distinct<T>(values: T[]): T[] {
    if (isEmpty(values)) {
        return [];
    } else {
        if (commonHelpers.isPrimitive(values[0])) {
            // Use built-in Javascript functionality to get distinct primitive values
            return Array.from(new Set(values));
        } else {
            // Call a function that uses deep-equal to check complex types
            return values.reduce((distinctValues: T[], currentValue: T) => {
                if (
                    !commonHelpers.isEqualToAnyItem(
                        currentValue,
                        distinctValues
                    )
                ) {
                    distinctValues.push(currentValue);
                }
                return distinctValues;
            }, []);
        }
    }
}

export function isEqual(array1: any[], array2: any[]): boolean {
    return deepEqual(array1, array2);
}

export function groupArray<T, S>(array: T[], keyGetter: (item: T) => S): T[][] {
    const keys: S[] = distinct(array.map(keyGetter));
    return keys.map(key => array.filter(x => keyGetter(x) === key));
}

export function arraysContainSameElements<T>(
    array1: T[],
    array2: T[]
): boolean {
    return (
        array2.length === array1.length &&
        intersect(array1, array2).length === array1.length
    );
}

export function arrayToObject<T>(value: T | T[]): T {
    if (Array.isArray(value)) {
        if (isEmpty(value)) {
            return {} as T;
        }
        return value.reduce((obj, item) => {
            Object.keys(item).forEach(prop => {
                if (commonHelpers.isDefined(item[prop])) {
                    obj[prop] = item[prop];
                }
            }, {});
            return obj;
        });
    }
    return value;
}

export function replaceArrayItem<T, S>(
    array: T[],
    idGetter: (item: T) => S,
    newItem: T
): T[] {
    if (isEmpty(array)) {
        return array;
    }
    const itemIndex: number = array.findIndex(item =>
        deepEqual(idGetter(item), idGetter(newItem))
    );
    if (itemIndex === -1) {
        return [...array];
    }
    return [
        ...array.slice(0, itemIndex),
        newItem,
        ...array.slice(itemIndex + 1),
    ];
}
