import {CommonModule} from '@angular/common';
import {HttpClientModule} from '@angular/common/http';
import {NgModule} from '@angular/core';
import {ChartModule} from 'angular2-highcharts';

import {BigNumberPipe} from './big-number/big-number.pipe';
import {CategorizedSelectComponent} from './categorized-select/categorized-select.component';
import {CategorizedTagsListComponent} from './categorized-tags-list/categorized-tags-list.component';
import {DropdownDirective} from './dropdown/dropdown.directive';
import {DropdownToggleDirective} from './dropdown/dropdown-toggle.directive';

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
    ],
    exports: [
        CommonModule,
        ChartModule,
        BigNumberPipe,
        CategorizedSelectComponent,
        CategorizedTagsListComponent,
        DropdownDirective,
        DropdownToggleDirective,
    ],
})
export class SharedModule {}
