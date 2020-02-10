import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {ConversionPixelsComponent} from './components/conversion-pixels/conversion-pixels.component';
import {CustomAudiencesComponent} from './components/custom-audiences/custom-audiences.component';
import {PixelsLibraryView} from './views/pixels-library/pixels-library.view';

@NgModule({
    declarations: [
        ConversionPixelsComponent,
        CustomAudiencesComponent,
        PixelsLibraryView,
    ],
    imports: [SharedModule],
    entryComponents: [PixelsLibraryView],
})
export class PixelsLibraryModule {}
