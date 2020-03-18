import {isDefined} from './common.helpers';
import * as moment from 'moment';

export function dateTimeFormatter(
    format: string
): (params: {value: Date}) => string {
    return params => {
        const value: Date = params.value;
        if (isDefined(value)) {
            return moment(value).format(format);
        }
        return 'N/A';
    };
}

export function booleanFormatter(params: {value: boolean}): string | string {
    const value: boolean = params.value;
    if (isDefined(value)) {
        return value === true ? 'Yes' : 'No';
    }
    return 'N/A';
}
