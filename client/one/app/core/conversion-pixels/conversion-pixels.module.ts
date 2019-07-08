import {NgModule} from '@angular/core';
import {ConversionPixelsService} from './services/conversion-pixels.service';
import {ConversionPixelsEndpoint} from './services/conversion-pixels.endpoint';

@NgModule({
    providers: [ConversionPixelsService, ConversionPixelsEndpoint],
})
export class ConversionPixelsModule {}
