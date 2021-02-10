import './creatives-grid.component.less';

import {
    ChangeDetectionStrategy,
    Component,
    EventEmitter,
    Input,
    OnChanges,
    Output,
    SimpleChanges,
} from '@angular/core';
import {Creative} from '../../../../../core/creatives/types/creative';
import {PaginationOptions} from '../../../../../shared/components/smart-grid/types/pagination-options';
import {PaginationState} from '../../../../../shared/components/smart-grid/types/pagination-state';
import {CreativesComponent} from '../creatives/creatives.component';
import {SmartGridColDef} from '../../../../../shared/components/smart-grid/types/smart-grid-col-def';
import {DetailGridInfo, GridApi, GridOptions} from 'ag-grid-community';
import {
    COLUMN_ACTIONS,
    COLUMN_SCOPE,
    COLUMN_SELECT,
    COLUMN_TAGS,
    COLUMN_TITLE,
    COLUMN_TYPE,
    refreshSelectColumn,
} from './creatives-grid.component.config';
import {HeaderCellComponent} from '../../../../../shared/components/smart-grid/components/cells/header-cell/header-cell.component';

@Component({
    selector: 'zem-creatives-grid',
    templateUrl: './creatives-grid.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreativesGridComponent implements OnChanges {
    @Input()
    creatives: Creative[];
    @Input()
    paginationCount: number;
    @Input()
    paginationOptions: PaginationOptions;
    @Input()
    context: {componentParent: CreativesComponent};
    @Input()
    isLoading: boolean;
    @Output()
    paginationChange: EventEmitter<PaginationState> = new EventEmitter<
        PaginationState
    >();

    columnDefs: SmartGridColDef[] = [
        COLUMN_SELECT,
        COLUMN_TITLE,
        COLUMN_TAGS,
        COLUMN_SCOPE,
        COLUMN_TYPE,
        COLUMN_ACTIONS,
    ];

    gridOptions: GridOptions = {
        immutableData: true,
        suppressChangeDetection: true,
        getRowNodeId: this.getRowNodeId,
        rowHeight: 72,
        frameworkComponents: {
            agColumnHeader: HeaderCellComponent,
        },
    };

    private gridApi: GridApi;

    ngOnChanges(changes: SimpleChanges) {
        if (this.gridApi && changes.creatives) {
            refreshSelectColumn(this.gridApi);
        }
    }

    onGridReady($event: DetailGridInfo) {
        this.gridApi = $event.api;
    }

    private getRowNodeId(creative: Creative): string {
        return creative.id;
    }
}
