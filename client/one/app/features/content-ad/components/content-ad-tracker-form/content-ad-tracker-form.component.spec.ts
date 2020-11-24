import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SharedModule} from '../../../../shared/shared.module';
import {ContentAdTrackerFormComponent} from './content-ad-tracker-form.component';

describe('ContentAdTrackerFormComponent', () => {
    let component: ContentAdTrackerFormComponent;
    let fixture: ComponentFixture<ContentAdTrackerFormComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [ContentAdTrackerFormComponent],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(ContentAdTrackerFormComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
