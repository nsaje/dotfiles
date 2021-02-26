import {NgModule} from '@angular/core';

import {SharedModule} from '../../../shared/shared.module';
import {CreativesComponent} from './components/creatives/creatives.component';
import {CreativesActionsComponent} from './components/creatives-actions/creatives-actions.component';
import {CreativesGridComponent} from './components/creatives-grid/creatives-grid.component';
import {CreativeActionsCellComponent} from './components/creative-actions-cell/creative-actions-cell.component';
import {CreativeBatchComponent} from './components/creative-batch/creative-batch.component';
import {CreativeTagsCellComponent} from './components/creative-tags-cell/creative-tags-cell.component';
import {CreativeCandidateComponent} from './components/creative-candidate/creative-candidate.component';
import {CreativeCandidateEditFormComponent} from './components/creative-candidate-edit-form/creative-candidate-edit-form.component';
import {TrackerFormComponent} from './components/tracker-form/tracker-form.component';
import {TrackersComponent} from './components/trackers/trackers.component';
import {TrackerComponent} from './components/tracker/tracker.component';
import {TrackersFormGroupComponent} from './components/trackers-form-group/trackers-form-group.component';

const EXPORTED_DECLARATIONS = [
    CreativesComponent,
    CreativesActionsComponent,
    CreativesGridComponent,
    CreativeActionsCellComponent,
    CreativeBatchComponent,
    CreativeTagsCellComponent,
    CreativeCandidateComponent,
    CreativeCandidateEditFormComponent,
    TrackerFormComponent,
    TrackersComponent,
    TrackerComponent,
    TrackersFormGroupComponent,
    CreativeCandidateEditFormComponent,
];

@NgModule({
    imports: [SharedModule],
    entryComponents: [
        CreativeActionsCellComponent,
        CreativeTagsCellComponent,
        TrackersComponent,
    ],
    declarations: EXPORTED_DECLARATIONS,
    exports: EXPORTED_DECLARATIONS,
})
export class CreativesSharedModule {}
