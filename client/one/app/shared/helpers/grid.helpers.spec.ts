import * as gridHelpers from './grid.helpers';

describe('gridHelpers', () => {
    it('should correctly format boolean values', () => {
        const formatter = gridHelpers.booleanFormatter;

        let gridValue = {value: true};
        expect(formatter(gridValue)).toEqual('Yes');

        gridValue = {value: false};
        expect(formatter(gridValue)).toEqual('No');

        gridValue = {value: null};
        expect(formatter(gridValue)).toEqual('N/A');

        gridValue = {value: undefined};
        expect(formatter(gridValue)).toEqual('N/A');
    });

    it('should correctly format dates', () => {
        let formatter = gridHelpers.dateTimeFormatter('DD.MM.YYYY');

        let gridValue = {value: new Date(2020, 2, 16, 13, 37)};
        expect(formatter(gridValue)).toEqual('16.03.2020');

        formatter = gridHelpers.dateTimeFormatter('M/D/YYYY h:mm A');
        expect(formatter(gridValue)).toEqual('3/16/2020 1:37 PM');

        gridValue = {value: null};
        expect(formatter(gridValue)).toEqual('N/A');

        gridValue = {value: undefined};
        expect(formatter(gridValue)).toEqual('N/A');
    });
});
