import * as commonHelpers from './common.helpers';

export function isEmpty(value: any[]): boolean {
    if (!commonHelpers.isDefined(value)) {
        return true;
    }
    return value.length === 0;
}
