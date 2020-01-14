import {CommonModule} from '@angular/common';
import {HttpClientModule} from '@angular/common/http';
import {NgModule} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {PortalModule} from '@angular/cdk/portal';
import {HighchartsChartModule} from 'highcharts-angular';
import {
    NgbDatepickerModule,
    NgbPopoverModule,
    NgbPaginationModule,
} from '@ng-bootstrap/ng-bootstrap';
import {NgSelectModule} from '@ng-select/ng-select';
import {NgOptionHighlightModule} from '@ng-select/ng-option-highlight';
import {NgxFileDropModule} from 'ngx-file-drop';
import {AgGridModule} from 'ag-grid-angular';

import {BigNumberPipe} from './pipes/big-number.pipe';
import {FilterKeydownEventDirective} from './directives/filter-keydown-event/filter-keydown-event.directive';
import {FocusDirective} from './directives/focus/focus.directive';
import {CategorizedSelectComponent} from './components/categorized-select/categorized-select.component';
import {CategorizedTagsListComponent} from './components/categorized-tags-list/categorized-tags-list.component';
import {DropdownDirective} from './components/dropdown/dropdown.directive';
import {DropdownToggleDirective} from './components/dropdown/dropdown-toggle.directive';
import {HelpPopoverComponent} from './components/help-popover/help-popover.component';
import {DaypartingInputComponent} from './components/dayparting-input/dayparting-input.component';
import {DrawerComponent} from './components/drawer/drawer.component';
import {IntegerInputComponent} from './components/integer-input/integer-input.component';
import {IntegerFormGroupComponent} from './components/integer-form-group/integer-form-group.component';
import {DecimalInputComponent} from './components/decimal-input/decimal-input.component';
import {DecimalFormGroupComponent} from './components/decimal-form-group/decimal-form-group.component';
import {CurrencyInputComponent} from './components/currency-input/currency-input.component';
import {CurrencyFormGroupComponent} from './components/currency-form-group/currency-form-group.component';
import {DateInputComponent} from './components/date-input/date-input.component';
import {DateFormGroupComponent} from './components/date-form-group/date-form-group.component';
import {SelectInputComponent} from './components/select-input/select-input.component';
import {SelectFormGroupComponent} from './components/select-form-group/select-form-group.component';
import {PrefixedInputComponent} from './components/prefixed-input/prefixed-input.component';
import {TextInputComponent} from './components/text-input/text-input.component';
import {TextFormGroupComponent} from './components/text-form-group/text-form-group.component';
import {TextAreaFormGroupComponent} from './components/textarea-form-group/textarea-form-group.component';
import {BidModifierInputComponent} from './components/bid-modifier-input/bid-modifier-input.component';
import {PopoverDirective} from './components/popover/popover.directive';
import {ModalComponent} from './components/modal/modal.component';
import {CheckboxInputComponent} from './components/checkbox-input/checkbox-input.component';
import {CheckboxFormGroupComponent} from './components/checkbox-form-group/checkbox-form-group.component';
import {RadioInputComponent} from './components/radio-input/radio-input.component';
import {InternalFeatureDirective} from './directives/internal-feature/internal-feature.directive';
import {FileSelectorComponent} from './components/file-selector/file-selector.component';
import {CommentPopoverComponent} from './components/comment-popover/comment-popover.component';
import {PaginationComponent} from './components/pagination/pagination.component';
import {SmartGridComponent} from './components/smart-grid/smart-grid.component';
import {LoadingOverlayComponent} from './components/smart-grid/components/loading-overlay/loading-overlay.component';
import {NoRowsOverlayComponent} from './components/smart-grid/components/no-rows-overlay/no-rows-overlay.component';
import {HelpPopoverHeaderComponent} from './components/smart-grid/components/header/help-popover/help-popover-header.component';
import {DealEditFormComponent} from './components/deal-edit-form/deal-edit-form.component';
import {SelectListComponent} from './components/select-list/select-list.component';
import {TextHighlightDirective} from './directives/text-highlight/text-highlight.directive';
import {ContentFormGroupComponent} from './components/content-form-group/content-form-group.component';
import {BidModifierTypesGridComponent} from './components/bid-modifier-types-grid/bid-modifier-types-grid.component';

const EXPORTED_DECLARATIONS = [
    // Pipes
    BigNumberPipe,

    // Directives
    FilterKeydownEventDirective,
    FocusDirective,
    PopoverDirective,
    InternalFeatureDirective,
    TextHighlightDirective,

    // Components
    CategorizedSelectComponent,
    CategorizedTagsListComponent,
    DropdownDirective,
    DropdownToggleDirective,
    DrawerComponent,
    DaypartingInputComponent,
    CheckboxInputComponent,
    CheckboxFormGroupComponent,
    RadioInputComponent,
    IntegerInputComponent,
    IntegerFormGroupComponent,
    DecimalInputComponent,
    DecimalFormGroupComponent,
    CurrencyInputComponent,
    CurrencyFormGroupComponent,
    DateInputComponent,
    DateFormGroupComponent,
    SelectInputComponent,
    SelectFormGroupComponent,
    PrefixedInputComponent,
    TextInputComponent,
    TextFormGroupComponent,
    TextAreaFormGroupComponent,
    BidModifierInputComponent,
    ModalComponent,
    HelpPopoverComponent,
    CommentPopoverComponent,
    FileSelectorComponent,
    ContentFormGroupComponent,
    PaginationComponent,
    SmartGridComponent,
    LoadingOverlayComponent,
    NoRowsOverlayComponent,
    HelpPopoverHeaderComponent,
    DealEditFormComponent,
    SelectListComponent,
    BidModifierTypesGridComponent,
];

@NgModule({
    imports: [
        CommonModule,
        HttpClientModule,
        FormsModule,
        PortalModule,
        HighchartsChartModule,
        NgbDatepickerModule,
        NgSelectModule,
        NgOptionHighlightModule,
        NgbPopoverModule,
        NgxFileDropModule,
        AgGridModule.withComponents([
            LoadingOverlayComponent,
            NoRowsOverlayComponent,
            HelpPopoverHeaderComponent,
        ]),
        NgbPaginationModule,
    ],
    declarations: EXPORTED_DECLARATIONS,
    exports: [
        CommonModule,
        FormsModule,
        PortalModule,
        HighchartsChartModule,
        ...EXPORTED_DECLARATIONS,
    ],
})
export class SharedModule {}
