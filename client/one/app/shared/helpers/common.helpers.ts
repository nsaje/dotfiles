import * as clone from 'clone';
import * as deepEqual from 'fast-deep-equal';
import * as arrayHelpers from './array.helpers';
import {Path} from 'Object/Path';

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

export function isNotEmpty(value: any): boolean {
    if (isDefined(value)) {
        if (Array.isArray(value)) {
            return (value as any[]).length > 0;
        } else if (typeof value === 'object') {
            return Object.keys(value).length > 0;
        } else {
            return !!value.toString();
        }
    }
    return false;
}

export function isEqualToAnyItem(value: any, items: any[]): boolean {
    if (!isDefined(items)) {
        return false;
    }
    if (!Array.isArray(items)) {
        return false;
    }

    return items.some(item => deepEqual(value, item));
}

export function isPrimitive(value: any) {
    return value !== Object(value);
}

export function getValueWithoutProps<
    T extends Object,
    S extends keyof Path<T, []> & string
>(value: T, props: S[]): Partial<T> {
    if (!isDefined(value)) {
        return value;
    }
    if (Array.isArray(value)) {
        return value;
    }
    if (typeof value !== 'object') {
        return value;
    }
    if (arrayHelpers.isEmpty(props)) {
        return value;
    }

    const formattedValue: any = {...value};
    props.forEach(prop => {
        if (Object.keys(formattedValue).includes(prop)) {
            delete formattedValue[prop];
        }
    });

    return formattedValue;
}

export function getValueWithOnlyProps<
    T extends Object,
    S extends keyof Path<T, []> & string
>(value: T, props: S[]): Partial<T> {
    if (!isDefined(value)) {
        return value;
    }
    if (Array.isArray(value)) {
        return value;
    }
    if (typeof value !== 'object') {
        return value;
    }

    const formattedValue: any = {...value};
    const newFormattedValue: any = {};
    props.forEach(prop => {
        if (Object.keys(formattedValue).includes(prop)) {
            newFormattedValue[prop] = formattedValue[prop];
        }
    });

    return newFormattedValue;
}

export function safeGet<T, S>(
    object: T | null | undefined,
    getter: (t: T) => S | undefined
): S | undefined {
    let result: S | undefined;
    if (isDefined(object)) {
        result = getter(object);
    }
    return result;
}

export function patchObject<T1, T2>(value: T1, patch: T2): any {
    if (!isDefined(value)) {
        return value;
    }
    if (typeof value !== 'object' || typeof patch !== 'object') {
        return value;
    }
    if (
        Object.prototype.toString.call(value) !==
        Object.prototype.toString.call(patch)
    ) {
        return value;
    }
    if (Array.isArray(value) && Array.isArray(patch)) {
        return [...value, ...patch];
    }
    return {
        ...value,
        ...patch,
    };
}
