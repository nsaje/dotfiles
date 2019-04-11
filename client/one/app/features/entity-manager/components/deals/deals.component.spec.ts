import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {DealsComponent} from './deals.component';

describe('DealsComponent', () => {
    let component: DealsComponent;
    let fixture: ComponentFixture<DealsComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [DealsComponent],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DealsComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
