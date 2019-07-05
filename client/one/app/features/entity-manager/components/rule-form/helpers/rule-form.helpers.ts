import {Unit} from '../rule-form.constants';

export function uuid(): string {
    return Math.floor((1 + Math.random()) * 0x10000)
        .toString(16)
        .substring(1);
}

export function getUnitText(unit: Unit): string {
    switch (unit) {
        case Unit.Percent:
            return '%';
        case Unit.Second:
            return 's';
        case Unit.CurrencySign:
            // TODO (automation-rules): Return correct currency symbol
            return '$';
        default:
            return '';
    }
}
