import {NgModule} from '@angular/core';
import {SharedModule} from '../../shared/shared.module';
import {ContentAdTrackerFormComponent} from './components/content-ad-tracker-form/content-ad-tracker-form.component';
import {ContentAdTrackerComponent} from './components/content-ad-tracker/content-ad-tracker.component';
import {ContentAdTrackersComponent} from './components/content-ad-trackers/content-ad-trackers.component';
@NgModule({
    declarations: [
        ContentAdTrackerFormComponent,
        ContentAdTrackersComponent,
        ContentAdTrackerComponent,
    ],
    imports: [SharedModule],
    providers: [],
    entryComponents: [ContentAdTrackersComponent],
})
export class ContentAdModule {}
