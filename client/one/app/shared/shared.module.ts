import {CommonModule} from '@angular/common';
import {HttpClientModule} from '@angular/common/http';
import {NgModule} from '@angular/core';
import {ChartModule} from 'angular2-highcharts';

import {BigNumberPipe} from './big-number/big-number.pipe';

@NgModule({
    imports: [
        CommonModule,
        HttpClientModule,
        ChartModule.forRoot(require('highcharts')),
    ],
    declarations: [
        BigNumberPipe,
    ],
    exports: [
        CommonModule,
        ChartModule,
        BigNumberPipe,
    ],
})
export class SharedModule {}
