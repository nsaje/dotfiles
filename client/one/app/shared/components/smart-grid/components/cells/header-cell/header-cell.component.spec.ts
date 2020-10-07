import {ComponentFixture, TestBed} from '@angular/core/testing';
import {ColDef, Column} from 'ag-grid-community';
import {HelpPopoverComponent} from '../../../../help-popover/help-popover.component';
import {PopoverDirective} from '../../../../popover/popover.directive';
import {HeaderCellComponent} from './header-cell.component';
import {DEFAULT_HEADER_CELL_SORT_ORDER} from './header-cell.component.config';
import {HeaderCellSort} from './header-cell.component.constants';
import {HeaderParams} from './types/header-params';

describe('HeaderCellComponent', () => {
    let component: HeaderCellComponent;
    let fixture: ComponentFixture<HeaderCellComponent>;
    let colDef: Partial<ColDef>;
    let field: string;
    let colId: string;
    let column: Partial<Column>;
    let params: Partial<HeaderParams>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                HeaderCellComponent,
                HelpPopoverComponent,
                PopoverDirective,
            ],
        });

        field = 'test_field';
        colId = 'test_field_id';
        colDef = {
            field: field,
            sortingOrder: null,
        };
        column = {
            getColDef: () => {
                return colDef;
            },
            getColId: () => {
                return colId;
            },
            getSort: () => {
                return null;
            },
        };
        params = {
            sortOptions: {
                sortType: 'server',
                initialSort: HeaderCellSort.DESC,
            },
            popoverTooltip: 'test popover text',
            popoverPlacement: 'top',
        };
        (params.column as any) = column;
    });

    beforeEach(() => {
        fixture = TestBed.createComponent<HeaderCellComponent>(
            HeaderCellComponent
        );
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
        component.agInit(params as HeaderParams);

        expect(component.params).toEqual(params as HeaderParams);
        expect(component.colDef).toEqual(colDef);
        expect(component.colId).toEqual(colId);
        expect(component.field).toEqual(field);
        expect(component.sort).toEqual(null);
        expect(component.sortingOrder).toEqual(DEFAULT_HEADER_CELL_SORT_ORDER);
    });
});
