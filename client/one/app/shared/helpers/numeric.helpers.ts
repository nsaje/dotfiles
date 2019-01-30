import * as commonHelpers from './common.helpers';

export function parseInteger(value: string): string {
    if (!commonHelpers.isDefined(value)) {
        return value;
    }
    return value.replace(/[^\d]+/g, '');
}

export function parseDecimal(value: string, fractionSize: number = 2): string {
    if (!commonHelpers.isDefined(value)) {
        return value;
    }

    const holder = value.replace(/[^\d.]+/g, '');
    const chunks = holder.split('.');
    let result = chunks[0];
    if (chunks[1]) {
        result = `${result}.${chunks[1]}`;
    }

    return result !== '' ? parseFloat(result).toFixed(fractionSize) : result;
}
