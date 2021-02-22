import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SharedModule} from '../../../../../shared/shared.module';
import {TrackerFormComponent} from './tracker-form.component';

describe('TrackerFormComponent', () => {
    let component: TrackerFormComponent;
    let fixture: ComponentFixture<TrackerFormComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [TrackerFormComponent],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(TrackerFormComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
