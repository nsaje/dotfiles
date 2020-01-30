import * as commonHelpers from './common.helpers';

export function isEmpty(value: any[]): boolean {
    if (!commonHelpers.isDefined(value)) {
        return true;
    }
    return value.length === 0;
}

export function intersect<T>(array1: T[], array2: T[]) {
    let intersection: T[] = [];
    if (!isEmpty(array1) && !isEmpty(array2)) {
        if (commonHelpers.isPrimitive(array1[0])) {
            // Do a fast and simple check for primitive types
            intersection = array1.filter(v1 => array2.includes(v1));
        } else {
            // Call a function that uses deep-equal to check complex types
            intersection = array1.filter(v1 =>
                commonHelpers.isEqualToAnyItem(v1, array2)
            );
        }
    }

    return intersection;
}

export function includesAny<T>(array1: T[], array2: T[]) {
    return intersect(array1, array2).length > 0;
}
