import {CommonModule} from '@angular/common';
import {HttpClientModule} from '@angular/common/http';
import {NgModule} from '@angular/core';
import {ChartModule} from 'angular2-highcharts';

import {BigNumberPipe} from './big-number/big-number.pipe';
import {CategorizedSelectComponent} from './categorized-select/categorized-select.component';
import {CategorizedTagsListComponent} from './categorized-tags-list/categorized-tags-list.component';
import {DropdownDirective} from './dropdown/dropdown.directive';
import {DropdownToggleDirective} from './dropdown/dropdown-toggle.directive';
import {HelpPopoverComponent} from './help-popover/help-popover.component';

@NgModule({
    imports: [
        CommonModule,
        HttpClientModule,
        ChartModule.forRoot(require('highcharts')),
    ],
    declarations: [
        BigNumberPipe,
        CategorizedSelectComponent,
        CategorizedTagsListComponent,
        DropdownDirective,
        DropdownToggleDirective,

        // Upgraded AngularJS components/ directives
        HelpPopoverComponent,
    ],
    exports: [
        CommonModule,
        ChartModule,
        BigNumberPipe,
        CategorizedSelectComponent,
        CategorizedTagsListComponent,
        DropdownDirective,
        DropdownToggleDirective,

        // Upgraded AngularJS components/ directives
        HelpPopoverComponent,
    ],
})
export class SharedModule {}
