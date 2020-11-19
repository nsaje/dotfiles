import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {CreativeLibraryView} from './views/creative-library/creative-library.view';

@NgModule({
    declarations: [CreativeLibraryView],
    imports: [SharedModule],
    entryComponents: [CreativeLibraryView],
})
export class CreativeLibraryModule {}
