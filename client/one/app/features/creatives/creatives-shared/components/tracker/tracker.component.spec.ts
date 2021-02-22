import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SharedModule} from '../../../../../shared/shared.module';
import {TrackerComponent} from './tracker.component';

describe('TrackerComponent', () => {
    let component: TrackerComponent;
    let fixture: ComponentFixture<TrackerComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [TrackerComponent],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(TrackerComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
