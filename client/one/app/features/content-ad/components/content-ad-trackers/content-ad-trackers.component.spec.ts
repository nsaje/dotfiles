import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SharedModule} from '../../../../shared/shared.module';
import {ContentAdTrackerFormComponent} from '../content-ad-tracker-form/content-ad-tracker-form.component';
import {ContentAdTrackerComponent} from '../content-ad-tracker/content-ad-tracker.component';
import {ContentAdTrackersComponent} from './content-ad-trackers.component';

describe('ContentAdTrackersComponent', () => {
    let component: ContentAdTrackersComponent;
    let fixture: ComponentFixture<ContentAdTrackersComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                ContentAdTrackersComponent,
                ContentAdTrackerComponent,
                ContentAdTrackerFormComponent,
            ],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(ContentAdTrackersComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
