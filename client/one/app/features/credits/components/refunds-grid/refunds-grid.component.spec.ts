import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SharedModule} from '../../../../shared/shared.module';
import {RefundsGridComponent} from './refunds-grid.component';

describe('RefundsGridComponent', () => {
    let component: RefundsGridComponent;
    let fixture: ComponentFixture<RefundsGridComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [RefundsGridComponent],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(RefundsGridComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
