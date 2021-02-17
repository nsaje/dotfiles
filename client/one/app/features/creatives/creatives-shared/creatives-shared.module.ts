import {NgModule} from '@angular/core';

import {SharedModule} from '../../../shared/shared.module';
import {CreativesComponent} from './components/creatives/creatives.component';
import {CreativesActionsComponent} from './components/creatives-actions/creatives-actions.component';
import {CreativesGridComponent} from './components/creatives-grid/creatives-grid.component';
import {CreativeActionsCellComponent} from './components/creative-actions-cell/creative-actions-cell.component';
import {CreativeBatchComponent} from './components/creative-batch/creative-batch.component';
import {CreativeTagsCellComponent} from './components/creative-tags-cell/creative-tags-cell.component';
import {CreativeCandidateComponent} from './components/creative-candidate/creative-candidate.component';

const EXPORTED_DECLARATIONS = [
    CreativesComponent,
    CreativesActionsComponent,
    CreativesGridComponent,
    CreativeActionsCellComponent,
    CreativeBatchComponent,
    CreativeTagsCellComponent,
    CreativeCandidateComponent,
];

@NgModule({
    imports: [SharedModule],
    entryComponents: [CreativeActionsCellComponent, CreativeTagsCellComponent],
    declarations: EXPORTED_DECLARATIONS,
    exports: EXPORTED_DECLARATIONS,
})
export class CreativesSharedModule {}
