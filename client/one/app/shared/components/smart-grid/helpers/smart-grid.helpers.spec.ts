import * as smartGridHelpers from './smart-grid.helpers';

it('should correctly compute approximate column width', () => {
    const MIN_COLUMN_WIDTH = 50;
    const MAX_COLUMN_WIDTH = 300;

    expect(
        smartGridHelpers.getApproximateColumnWidth(
            '',
            MIN_COLUMN_WIDTH,
            MAX_COLUMN_WIDTH
        )
    ).toEqual(MIN_COLUMN_WIDTH);
    expect(
        smartGridHelpers.getApproximateColumnWidth(
            null,
            MIN_COLUMN_WIDTH,
            MAX_COLUMN_WIDTH
        )
    ).toEqual(MIN_COLUMN_WIDTH);
    expect(
        smartGridHelpers.getApproximateColumnWidth(
            undefined,
            MIN_COLUMN_WIDTH,
            MAX_COLUMN_WIDTH
        )
    ).toEqual(MIN_COLUMN_WIDTH);
    expect(
        smartGridHelpers.getApproximateColumnWidth(
            'Test Column Name',
            MIN_COLUMN_WIDTH,
            MAX_COLUMN_WIDTH
        )
    ).toEqual(127);
    expect(
        smartGridHelpers.getApproximateColumnWidth(
            'Test Column Name',
            MIN_COLUMN_WIDTH,
            MAX_COLUMN_WIDTH,
            true,
            false,
            false
        )
    ).toEqual(147);
    expect(
        smartGridHelpers.getApproximateColumnWidth(
            'Test Column Name',
            MIN_COLUMN_WIDTH,
            MAX_COLUMN_WIDTH,
            true,
            true,
            false
        )
    ).toEqual(167);
    expect(
        smartGridHelpers.getApproximateColumnWidth(
            'Test Column Name',
            MIN_COLUMN_WIDTH,
            MAX_COLUMN_WIDTH,
            true,
            true,
            true
        )
    ).toEqual(187);
});
