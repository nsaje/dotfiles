import {ComponentFixture, TestBed} from '@angular/core/testing';
import {ColDef, Column} from 'ag-grid-community';
import {InternalFeatureDirective} from '../../../../../directives/internal-feature/internal-feature.directive';
import {CheckboxInputComponent} from '../../../../checkbox-input/checkbox-input.component';
import {HelpPopoverComponent} from '../../../../help-popover/help-popover.component';
import {PopoverDirective} from '../../../../popover/popover.directive';
import {HeaderCellComponent} from './header-cell.component';
import {
    DEFAULT_HEADER_CELL_SORT_ORDER,
    DEFAULT_HEADER_PARAMS,
} from './header-cell.component.config';
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
                InternalFeatureDirective,
                CheckboxInputComponent,
            ],
        });

        field = 'test_field';
        colId = 'test_field_id';
        colDef = {
            field: field,
            sort: null,
        };
        column = {
            getColDef: () => {
                return colDef;
            },
            getColId: () => {
                return colId;
            },
        };
        params = {
            enableSorting: true,
            sortOptions: {
                sortType: 'server',
                initialSort: HeaderCellSort.DESC,
            },
            enableSelection: true,
            selectionOptions: {
                isChecked: (params: HeaderParams) => true,
                isDisabled: (params: HeaderParams) => false,
                setChecked: (value: boolean, params: HeaderParams) => {},
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

        const componentParams = {
            ...DEFAULT_HEADER_PARAMS,
            ...params,
        };

        expect(component.params).toEqual(componentParams as HeaderParams);
        expect(component.colDef).toEqual(colDef);
        expect(component.colId).toEqual(colId);
        expect(component.field).toEqual(field);
        expect(component.sort).toEqual(null);
        expect(component.sortingOrder).toEqual(DEFAULT_HEADER_CELL_SORT_ORDER);
        expect(component.isChecked).toEqual(true);
        expect(component.isCheckboxDisabled).toEqual(false);
    });
});
