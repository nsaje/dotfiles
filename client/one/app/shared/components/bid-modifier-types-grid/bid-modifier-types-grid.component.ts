import './bid-modifier-types-grid.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    OnChanges,
    OnInit,
    SimpleChanges,
    Output,
    EventEmitter,
} from '@angular/core';
import {SelectionChangedEvent, DetailGridInfo} from 'ag-grid-community';
import {BidModifierTypesGridStore} from './services/bid-modifier-types-grid.store';
import {TypeSummaryGridRow} from './services/type-summary-grid-row';
import * as commonHelpers from '../../helpers/common.helpers';

@Component({
    selector: 'zem-bid-modifier-types-grid',
    templateUrl: './bid-modifier-types-grid.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [BidModifierTypesGridStore],
})
export class BidModifierTypesGridComponent implements OnChanges, OnInit {
    @Input()
    showCountColumn: boolean = true;
    @Input()
    selectableRows: boolean = false;
    @Input()
    selectionTooltip: string;
    @Input()
    autoSelectAllRows: boolean = false;
    @Input()
    typeSummaryGridRows: TypeSummaryGridRow[];
    @Output()
    selectedTypeSummaryGridRows = new EventEmitter<TypeSummaryGridRow[]>();

    constructor(public store: BidModifierTypesGridStore) {}

    ngOnInit(): void {
        this.store.updateGridConfig(
            this.showCountColumn,
            this.selectableRows,
            this.selectionTooltip
        );
        this.store.updateTypeSummaryGridRows(this.typeSummaryGridRows);
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.showCountColumn || changes.selectableRows) {
            this.store.updateGridConfig(
                this.showCountColumn,
                this.selectableRows,
                this.selectionTooltip
            );
        }
        if (changes.bidModifierTypeSummaries) {
            this.store.updateTypeSummaryGridRows(this.typeSummaryGridRows);
        }
    }

    onSelectionChanged(event: any[]): void {
        const selectedRows = event as TypeSummaryGridRow[];
        this.selectedTypeSummaryGridRows.emit(selectedRows);
    }

    onGridReady(event: DetailGridInfo) {
        if (commonHelpers.isDefined(event.api)) {
            if (this.autoSelectAllRows) {
                event.api.selectAll();
            }
        }
    }
}
