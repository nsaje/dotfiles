// tslint:disable: no-var-requires
const isPlainObject = require('lodash.isplainobject');
const transform = require('lodash.transform');
// tslint:enable: no-var-requires

import {DeepCleanConfig} from '../types/deep-clean-config';
import * as commonHelpers from './common.helpers';

export default function deepClean<T>(
    object: T,
    {
        cleanKeys = [],
        cleanValues = [],
        emptyArrays = true,
        emptyObjects = true,
        emptyStrings = true,
        nullValues = true,
        undefinedValues = true,
    }: DeepCleanConfig = {}
): Partial<T> {
    // tslint:disable-next-line: cyclomatic-complexity
    return transform(object, (result: any, value: any, key: any) => {
        // Exclude specific keys.
        if (cleanKeys.includes(key)) {
            return;
        }

        // Recurse into arrays and objects.
        if (Array.isArray(value) || isPlainObject(value)) {
            value = deepClean(value, {
                cleanKeys,
                cleanValues,
                emptyArrays,
                emptyObjects,
                emptyStrings,
                nullValues,
                undefinedValues,
            });
        }

        // Exclude specific values.
        if (cleanValues.includes(value)) {
            return;
        }

        // Exclude empty objects.
        if (
            emptyObjects &&
            isPlainObject(value) &&
            !commonHelpers.isNotEmpty(value)
        ) {
            return;
        }

        // Exclude empty arrays.
        if (emptyArrays && Array.isArray(value) && !value.length) {
            return;
        }

        // Exclude empty strings.
        if (emptyStrings && value === '') {
            return;
        }

        // Exclude null values.
        if (nullValues && value === null) {
            return;
        }

        // Exclude undefined values.
        if (undefinedValues && value === undefined) {
            return;
        }

        // Append when recursing arrays.
        if (Array.isArray(result)) {
            return result.push(value);
        }

        result[key] = value;
    });
}
