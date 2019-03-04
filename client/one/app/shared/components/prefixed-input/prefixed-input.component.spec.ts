import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {PrefixedInputComponent} from './prefixed-input.component';

describe('PrefixedInputComponent', () => {
    let component: PrefixedInputComponent;
    let fixture: ComponentFixture<PrefixedInputComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [PrefixedInputComponent],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(PrefixedInputComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
