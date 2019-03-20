import {CommonModule} from '@angular/common';
import {HttpClientModule} from '@angular/common/http';
import {NgModule} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {PortalModule} from '@angular/cdk/portal';
import {ChartModule} from 'angular2-highcharts';
import {
    NgbDatepickerModule,
    NgbPopoverModule,
} from '@ng-bootstrap/ng-bootstrap';
import {NgSelectModule} from '@ng-select/ng-select';

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
import {DecimalInputComponent} from './components/decimal-input/decimal-input.component';
import {CurrencyInputComponent} from './components/currency-input/currency-input.component';
import {DateInputComponent} from './components/date-input/date-input.component';
import {SelectInputComponent} from './components/select-input/select-input.component';
import {PrefixedInputComponent} from './components/prefixed-input/prefixed-input.component';
import {BidModifierInputComponent} from './components/bid-modifier-input/bid-modifier-input.component';
import {PopoverDirective} from './components/popover/popover.directive';
import {CheckboxInputComponent} from './components/checkbox-input/checkbox-input.component';
import {RadioInputComponent} from './components/radio-input/radio-input.component';
import {InternalFeatureDirective} from './directives/internal-feature/internal-feature.directive';

const EXPORTED_DECLARATIONS = [
    BigNumberPipe,
    FilterKeydownEventDirective,
    FocusDirective,
    CategorizedSelectComponent,
    CategorizedTagsListComponent,
    DropdownDirective,
    DropdownToggleDirective,
    DrawerComponent,
    DaypartingInputComponent,
    CheckboxInputComponent,
    RadioInputComponent,
    IntegerInputComponent,
    DecimalInputComponent,
    CurrencyInputComponent,
    DateInputComponent,
    SelectInputComponent,
    PrefixedInputComponent,
    BidModifierInputComponent,
    PopoverDirective,
    HelpPopoverComponent,
    InternalFeatureDirective,
];

@NgModule({
    imports: [
        CommonModule,
        HttpClientModule,
        FormsModule,
        PortalModule,
        ChartModule.forRoot(require('highcharts')),
        NgbDatepickerModule,
        NgSelectModule,
        NgbPopoverModule,
    ],
    declarations: EXPORTED_DECLARATIONS,
    exports: [
        CommonModule,
        FormsModule,
        PortalModule,
        ChartModule,
        ...EXPORTED_DECLARATIONS,
    ],
})
export class SharedModule {}
