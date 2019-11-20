import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SharedModule} from '../../../../shared/shared.module';
import {DealComponent} from './deal.component';

describe('DealComponent', () => {
    let component: DealComponent;
    let fixture: ComponentFixture<DealComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [DealComponent],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DealComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
