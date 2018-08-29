import {MulticurrencyService} from './multicurrency.service';

declare var constants: any;

describe('MulticurrencyService', () => {
    let service: MulticurrencyService;

    const USD_ACCOUNT = {data: {currency: constants.currency.USD}};
    const EUR_ACCOUNT = {data: {currency: constants.currency.EUR}};

    beforeEach(() => {
        service = new MulticurrencyService();
    });

    it('should return correctly formatted value in appropriate currency', () => {
        expect(service.getValueInAppropriateCurrency(2.5, USD_ACCOUNT)).toEqual(
            '$2.50'
        );
        expect(
            service.getValueInAppropriateCurrency(2.00006, USD_ACCOUNT, 4)
        ).toEqual('$2.0001');
        expect(
            service.getValueInAppropriateCurrency(2000.00006, USD_ACCOUNT, 4)
        ).toEqual('$2,000.0001');
        expect(service.getValueInAppropriateCurrency(2.5, EUR_ACCOUNT)).toEqual(
            '€2.50'
        );
        expect(
            service.getValueInAppropriateCurrency(2000.00006, EUR_ACCOUNT, 4)
        ).toEqual('€2,000.0001');
    });

    it('should return correct currency symbol', () => {
        expect(service.getAppropriateCurrencySymbol(USD_ACCOUNT)).toEqual('$');
        expect(service.getAppropriateCurrencySymbol(EUR_ACCOUNT)).toEqual('€');
    });

    it('should return correct currency', () => {
        expect(service.getAppropriateCurrency(USD_ACCOUNT)).toEqual(
            constants.currency.USD
        );
        expect(service.getAppropriateCurrency(EUR_ACCOUNT)).toEqual(
            constants.currency.EUR
        );
    });
});
