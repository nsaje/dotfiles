import {CommonModule} from '@angular/common';
import {HttpClientModule} from '@angular/common/http';
import {NgModule} from '@angular/core';
import {ChartModule} from 'angular2-highcharts';

import {BigNumberPipe} from './big-number/big-number.pipe';
import {CategorizedTagsListComponent} from './categorized-tags-list/categorized-tags-list.component';

@NgModule({
    imports: [
        CommonModule,
        HttpClientModule,
        ChartModule.forRoot(require('highcharts')),
    ],
    declarations: [
        BigNumberPipe,
        CategorizedTagsListComponent,
    ],
    exports: [
        CommonModule,
        ChartModule,
        BigNumberPipe,
        CategorizedTagsListComponent,
    ],
})
export class SharedModule {}
