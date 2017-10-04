import {CommonModule} from '@angular/common';
import {HttpClientModule} from '@angular/common/http';
import {NgModule} from '@angular/core';

import {BigNumberPipe} from './big-number/big-number.pipe';

@NgModule({
    imports: [
        CommonModule,
        HttpClientModule,
    ],
    declarations: [
        BigNumberPipe,
    ],
    exports: [
        CommonModule,
        BigNumberPipe,
    ],
})
export class SharedModule {}
