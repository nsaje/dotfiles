import * as currencyHelpers from './currency.helpers';
import {Currency, Unit} from '../../app.constants';

export function getUnitText(unit: Unit, currency?: Currency): string {
    switch (unit) {
        case Unit.Percent:
            return '%';
        case Unit.Second:
            return 's';
        case Unit.CurrencySign:
            return currencyHelpers.getCurrencySymbol(currency);
        default:
            return '';
    }
}
