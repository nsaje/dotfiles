import * as clone from 'clone';
import * as deepEqual from 'fast-deep-equal';

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
