import {DateInputFormatter} from './date-input.formatter';
import {NgbDate, NgbDateStruct} from '@ng-bootstrap/ng-bootstrap';

describe('DateInputFormatter', () => {
    let formatter: DateInputFormatter;

    beforeEach(() => {
        formatter = new DateInputFormatter();
    });

    it('should correctly format NgbDate to string', () => {
        expect(formatter.format(new NgbDate(2019, 1, 5))).toEqual('01/05/2019');
        expect(formatter.format(new NgbDate(2019, 12, 31))).toEqual(
            '12/31/2019'
        );
        expect(formatter.format(null)).toEqual('');
        expect(formatter.format(undefined)).toEqual('');
    });

    it('should correctly parse string to NgbDate', () => {
        const ngbDate = new NgbDate(2019, 1, 5);
        expect(formatter.parse('01/05/2019')).toEqual({
            year: ngbDate.year,
            month: ngbDate.month,
            day: ngbDate.day,
        });
        expect(formatter.parse(null)).toEqual(null);
        expect(formatter.parse(undefined)).toEqual(null);
    });
});
