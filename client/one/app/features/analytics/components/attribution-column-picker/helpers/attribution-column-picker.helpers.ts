import {PixelOptionsColumn} from '../../../types/pixel-options-column';
import {ConversionWindow} from '../../../../../app.constants';

export function getFieldsToToggle(
    selectedColumns: PixelOptionsColumn[],
    substringToReplace: string | RegExp,
    substringReplacement: string
): string[] {
    const fieldsToToggle = [];
    for (const column of selectedColumns) {
        fieldsToToggle.push(column.field);
        fieldsToToggle.push(
            column.field.replace(substringToReplace, substringReplacement)
        );
    }
    return fieldsToToggle;
}

export function mapConversionWindowValue(window: ConversionWindow): number {
    switch (window) {
        case ConversionWindow.LEQ_1_DAY:
            return 24;
        case ConversionWindow.LEQ_7_DAYS:
            return 168;
        case ConversionWindow.LEQ_30_DAYS:
            return 720;
    }
}
