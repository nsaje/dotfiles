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
