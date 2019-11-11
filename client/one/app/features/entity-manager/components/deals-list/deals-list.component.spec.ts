import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SharedModule} from '../../../../shared/shared.module';
import {DealsListComponent} from './deals-list.component';

describe('DealsListComponent', () => {
    let component: DealsListComponent;
    let fixture: ComponentFixture<DealsListComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [DealsListComponent],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DealsListComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
