import {MulticurrencyService} from './multicurrency.service';
import {PermissionsServiceMock} from '../../test/mocks/permissions.service.mock';

declare var constants: any;

describe('MulticurrencyService', () => {
    let service: MulticurrencyService;

    const USD_ACCOUNT = {data: {currency: constants.currency.USD}};
    const EUR_ACCOUNT = {data: {currency: constants.currency.EUR}};

    describe('user has permissions', () => {
        beforeEach(() => {
            const mockedPermissionService = new PermissionsServiceMock();
            spyOn(mockedPermissionService, 'hasPermission').and.returnValue(true);
            service = new MulticurrencyService(mockedPermissionService);
        });

        it('should return correctly formatted value in appropriate currency', () => {
            expect(service.getValueInAppropriateCurrency(2.5, USD_ACCOUNT)).toEqual('$2.50');
            expect(service.getValueInAppropriateCurrency(2.00006, USD_ACCOUNT, [], 4)).toEqual('$2.0001');
            expect(service.getValueInAppropriateCurrency(2000.00006, USD_ACCOUNT, [], 4)).toEqual('$2,000.0001');
            expect(service.getValueInAppropriateCurrency(2.5, EUR_ACCOUNT)).toEqual('€2.50');
            expect(service.getValueInAppropriateCurrency(2000.00006, EUR_ACCOUNT, [], 4)).toEqual('€2,000.0001');
        });

        it('should return correct currency symbol', () => {
            expect(service.getAppropriateCurrencySymbol(USD_ACCOUNT)).toEqual('$');
            expect(service.getAppropriateCurrencySymbol(EUR_ACCOUNT)).toEqual('€');
        });
    });

    describe('user doesn\'t have permissions', () => {
        beforeEach(() => {
            const mockedPermissionService = new PermissionsServiceMock();
            spyOn(mockedPermissionService, 'hasPermission').and.returnValue(false);
            service = new MulticurrencyService(mockedPermissionService);
        });

        it('should return correctly formatted value in appropriate currency', () => {
            expect(service.getValueInAppropriateCurrency(2.5, USD_ACCOUNT)).toEqual('$2.50');
            expect(service.getValueInAppropriateCurrency(2.00006, USD_ACCOUNT, [], 4)).toEqual('$2.0001');
            expect(service.getValueInAppropriateCurrency(2000.00006, USD_ACCOUNT, [], 4)).toEqual('$2,000.0001');
            expect(service.getValueInAppropriateCurrency(2.5, EUR_ACCOUNT)).toEqual('$2.50');
            expect(service.getValueInAppropriateCurrency(2.00006, EUR_ACCOUNT, [], 4)).toEqual('$2.0001');
            expect(service.getValueInAppropriateCurrency(2000.00006, EUR_ACCOUNT, [], 4)).toEqual('$2,000.0001');
        });

        it('should return correct currency symbol', () => {
            expect(service.getAppropriateCurrencySymbol(USD_ACCOUNT)).toEqual('$');
            expect(service.getAppropriateCurrencySymbol(EUR_ACCOUNT)).toEqual('$');
        });
    });
});
