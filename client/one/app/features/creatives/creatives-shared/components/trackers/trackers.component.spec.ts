import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SharedModule} from '../../../../../shared/shared.module';
import {TrackerFormComponent} from '../tracker-form/tracker-form.component';
import {TrackerComponent} from '../tracker/tracker.component';
import {TrackersComponent} from './trackers.component';

describe('TrackersComponent', () => {
    let component: TrackersComponent;
    let fixture: ComponentFixture<TrackersComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                TrackersComponent,
                TrackerComponent,
                TrackerFormComponent,
            ],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(TrackersComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
