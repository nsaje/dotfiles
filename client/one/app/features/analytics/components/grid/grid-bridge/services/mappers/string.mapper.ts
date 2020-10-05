import {ColDef} from 'ag-grid-community';
import {Grid} from '../../types/grid';
import {GridColumn} from '../../types/grid-column';
import {ColumnMapper} from './column.mapper';
import * as commonHelpers from '../../../../../../../shared/helpers/common.helpers';

export class StringColumnMapper extends ColumnMapper {
    map(grid: Grid, column: GridColumn): ColDef {
        return {
            headerName: this.getHeaderName(column),
            field: this.getFieldName(column),
            valueFormatter: params => {
                const data = params.value;
                if (
                    commonHelpers.isDefined(data) &&
                    commonHelpers.isDefined(data.value)
                ) {
                    return data.value.toString();
                }
                return 'N/A';
            },
        };
    }

    private getHeaderName(column: GridColumn): string {
        if (commonHelpers.isDefined(column.data)) {
            return column.data.name;
        }
        return '';
    }

    private getFieldName(column: GridColumn): string {
        if (commonHelpers.isDefined(column.data)) {
            return column.data.field;
        }
        return '';
    }
}
