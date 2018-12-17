import {CommonModule} from '@angular/common';
import {HttpClientModule} from '@angular/common/http';
import {NgModule} from '@angular/core';
import {ChartModule} from 'angular2-highcharts';

import {BigNumberPipe} from './pipes/big-number.pipe';
import {CategorizedSelectComponent} from './components/categorized-select/categorized-select.component';
import {CategorizedTagsListComponent} from './components/categorized-tags-list/categorized-tags-list.component';
import {DropdownDirective} from './components/dropdown/dropdown.directive';
import {DropdownToggleDirective} from './components/dropdown/dropdown-toggle.directive';
import {HelpPopoverComponent} from './components/help-popover/help-popover.component';
import {DaypartingInputComponent} from './components/dayparting-input/dayparting-input.component';
import {DrawerComponent} from './components/drawer/drawer.component';

const EXPORTED_DECLARATIONS = [
    BigNumberPipe,
    CategorizedSelectComponent,
    CategorizedTagsListComponent,
    DropdownDirective,
    DropdownToggleDirective,
    DrawerComponent,
    DaypartingInputComponent,

    // Upgraded AngularJS components/ directives
    HelpPopoverComponent,
];

@NgModule({
    imports: [
        CommonModule,
        HttpClientModule,
        ChartModule.forRoot(require('highcharts')),
    ],
    declarations: EXPORTED_DECLARATIONS,
    exports: [CommonModule, ChartModule, ...EXPORTED_DECLARATIONS],
})
export class SharedModule {}
