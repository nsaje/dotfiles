import * as moment from 'moment';
import * as commonHelpers from './common.helpers';

export function convertDateToString(value: Date): string {
    if (!commonHelpers.isDefined(value)) {
        return null;
    }
    return moment(value).format('YYYY-MM-DD');
}

export function canConvertStringToDate(value: string): boolean {
    if (!commonHelpers.isDefined(value)) {
        return false;
    }
    return moment(value, 'YYYY-MM-DD', true).isValid();
}

export function convertStringToDate(value: string): Date {
    if (!canConvertStringToDate(value)) {
        return null;
    }
    return moment(value).toDate();
}

export function convertDateTimeToUTCString(value: Date): string {
    if (!commonHelpers.isDefined(value)) {
        return null;
    }
    return moment(value)
        .utc()
        .format('YYYY-MM-DD[T]HH:mm');
}
