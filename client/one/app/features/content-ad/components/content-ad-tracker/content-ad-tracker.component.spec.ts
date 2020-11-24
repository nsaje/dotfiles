import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SharedModule} from '../../../../shared/shared.module';
import {ContentAdTrackerComponent} from './content-ad-tracker.component';

describe('ContentAdTrackerComponent', () => {
    let component: ContentAdTrackerComponent;
    let fixture: ComponentFixture<ContentAdTrackerComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [ContentAdTrackerComponent],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(ContentAdTrackerComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
