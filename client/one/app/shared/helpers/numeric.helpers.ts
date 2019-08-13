import * as commonHelpers from './common.helpers';
import * as unitsHelpers from './units.helpers';
import {Unit} from '../../app.constants';

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

export function convertToPercentValue(
    value: string,
    includePercentUnit: boolean = true
): string {
    if (!commonHelpers.isNotEmpty(value)) {
        return null;
    }
    const numericValue = value.replace(/[^\d.]+/g, '');
    if (isNaN(Number.parseFloat(numericValue))) {
        return null;
    }

    const percentValue = (Number.parseFloat(numericValue) * 100).toFixed(2);
    return includePercentUnit
        ? `${percentValue}${unitsHelpers.getUnitText(Unit.Percent)}`
        : percentValue;
}

export function convertFromPercentValue(value: string): string {
    if (!commonHelpers.isNotEmpty(value)) {
        return null;
    }
    const numericValue = value.replace(/[^\d.]+/g, '');
    if (isNaN(Number.parseFloat(numericValue))) {
        return null;
    }

    return (Number.parseFloat(numericValue) / 100).toString();
}
