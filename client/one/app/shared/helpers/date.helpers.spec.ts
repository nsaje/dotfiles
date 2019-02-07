import * as dateHelpers from './date.helpers';
import * as moment from 'moment';

describe('DateHelpers', () => {
    it('should correctly check if string can be converted to date', () => {
        expect(dateHelpers.canConvertStringToDate(null)).toEqual(false);
        expect(dateHelpers.canConvertStringToDate(undefined)).toEqual(false);
        expect(dateHelpers.canConvertStringToDate('')).toEqual(false);
        expect(dateHelpers.canConvertStringToDate('Test')).toEqual(false);
        expect(dateHelpers.canConvertStringToDate('1234.56')).toEqual(false);
        expect(dateHelpers.canConvertStringToDate('2019-01-05')).toEqual(true);
    });

    it('should correctly convert string to date', () => {
        expect(dateHelpers.convertStringToDate(null)).toEqual(null);
        expect(dateHelpers.convertStringToDate(undefined)).toEqual(null);
        expect(dateHelpers.convertStringToDate('2019-01-05')).toEqual(
            moment('2019-01-05').toDate()
        );
        expect(dateHelpers.convertStringToDate('2019-11-05')).toEqual(
            moment('2019-11-05').toDate()
        );
    });

    it('should correctly convert date to string', () => {
        expect(dateHelpers.convertDateToString(null)).toEqual(null);
        expect(dateHelpers.convertDateToString(undefined)).toEqual(null);
        expect(
            dateHelpers.convertDateToString(moment('2019-01-05').toDate())
        ).toEqual('2019-01-05');
        expect(
            dateHelpers.convertDateToString(moment('2019-11-05').toDate())
        ).toEqual('2019-11-05');
    });
});
