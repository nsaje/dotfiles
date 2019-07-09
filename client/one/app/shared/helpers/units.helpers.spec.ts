import * as unitsHelpers from './units.helpers';
import {Unit, Currency} from '../../app.constants';
import * as currencyHelpers from './currency.helpers';

describe('unitsHelpers', () => {
    it('should return correct unit text for unit', () => {
        expect(unitsHelpers.getUnitText(null)).toEqual('');
        expect(unitsHelpers.getUnitText(Unit.Percent)).toEqual('%');
        expect(unitsHelpers.getUnitText(Unit.Second)).toEqual('s');
        expect(unitsHelpers.getUnitText(Unit.CurrencySign)).toEqual(
            currencyHelpers.getCurrencySymbol(Currency.USD)
        );
        expect(
            unitsHelpers.getUnitText(Unit.CurrencySign, Currency.EUR)
        ).toEqual(currencyHelpers.getCurrencySymbol(Currency.EUR));
    });
});
