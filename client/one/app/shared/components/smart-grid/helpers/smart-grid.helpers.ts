import * as commonHelpers from '../../../helpers/common.helpers';
import {
    HEADER_CELL_CHECKBOX_WIDTH,
    HEADER_CELL_FONT,
    HEADER_CELL_HELP_POPOVER_WIDTH,
    HEADER_CELL_PADDING,
    HEADER_CELL_SORT_ARROW_WIDTH,
} from '../smart-grid.component.constants';

export function getApproximateColumnWidth(
    headerName: string,
    minColumnWidth: number,
    maxColumnWidth: number,
    includeCheckboxWidth: boolean = false,
    includeHelpPopoverWidth: boolean = false,
    includeSortArrowWidth: boolean = false
): number {
    if (commonHelpers.isDefined(headerName)) {
        const element: HTMLCanvasElement = document.createElement('canvas');
        const context: CanvasRenderingContext2D = element.getContext('2d');
        context.font = HEADER_CELL_FONT;
        const textMetrics: TextMetrics = context.measureText(headerName);

        let columnWidth: number = textMetrics.width;
        columnWidth += 2 * HEADER_CELL_PADDING;

        if (includeCheckboxWidth) {
            columnWidth += HEADER_CELL_CHECKBOX_WIDTH;
        }
        if (includeHelpPopoverWidth) {
            columnWidth += HEADER_CELL_HELP_POPOVER_WIDTH;
        }
        if (includeSortArrowWidth) {
            columnWidth += HEADER_CELL_SORT_ARROW_WIDTH;
        }

        return Math.ceil(
            Math.min(maxColumnWidth, Math.max(minColumnWidth, columnWidth))
        );
    }
    return minColumnWidth;
}
