import * as commonHelpers from './common.helpers';

export function parseInteger(value: string): string {
    if (!commonHelpers.isDefined(value)) {
        return null;
    }
    return value.replace(/[^\d]+/g, '');
}

export function parseDecimal(value: string, fractionSize: number = 2): string {
    if (!commonHelpers.isDefined(value)) {
        return null;
    }

    const holder = value.replace(/[^-+\d.]+/g, '');
    const chunks = holder.split('.');
    let result = chunks[0];
    if (chunks[1]) {
        result = `${result}.${chunks[1]}`;
    }

    if (result === '-' || result === '+') {
        return (0.0).toFixed(fractionSize);
    }
    return result !== '' ? parseFloat(result).toFixed(fractionSize) : result;
}

export function getNumberSign(value: number): string {
    if (!commonHelpers.isDefined(value)) {
        return '';
    }
    if (value < 0) {
        return '-';
    }
    return '+';
}

export function validateMinMax(
    value: number,
    minValue: number,
    maxValue: number
): boolean {
    if (minValue && !isNaN(value) && minValue > value) {
        return false;
    }
    if (maxValue && !isNaN(value) && maxValue < value) {
        return false;
    }
    return true;
}
