import {CommonModule} from '@angular/common';
import {HttpClientModule} from '@angular/common/http';
import {NgModule} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {ChartModule} from 'angular2-highcharts';
import {NgbDatepickerModule} from '@ng-bootstrap/ng-bootstrap';
import {NgSelectModule} from '@ng-select/ng-select';

import {BigNumberPipe} from './pipes/big-number.pipe';
import {FilterKeydownEventDirective} from './directives/filter-keydown-event.directive';
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

const EXPORTED_DECLARATIONS = [
    BigNumberPipe,
    FilterKeydownEventDirective,
    CategorizedSelectComponent,
    CategorizedTagsListComponent,
    DropdownDirective,
    DropdownToggleDirective,
    DrawerComponent,
    DaypartingInputComponent,
    IntegerInputComponent,
    DecimalInputComponent,
    CurrencyInputComponent,
    DateInputComponent,
    SelectInputComponent,

    // Upgraded AngularJS components/ directives
    HelpPopoverComponent,
];

@NgModule({
    imports: [
        CommonModule,
        HttpClientModule,
        FormsModule,
        ChartModule.forRoot(require('highcharts')),
        NgbDatepickerModule,
        NgSelectModule,
    ],
    declarations: EXPORTED_DECLARATIONS,
    exports: [CommonModule, FormsModule, ChartModule, ...EXPORTED_DECLARATIONS],
})
export class SharedModule {}
