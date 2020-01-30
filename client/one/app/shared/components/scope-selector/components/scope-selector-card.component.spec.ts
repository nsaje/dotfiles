import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {ScopeSelectorCardComponent} from './scope-selector-card.component';
import {RadioInputComponent} from '../../radio-input/radio-input.component';

describe('ScopeSelectorCardComponent', () => {
    let component: ScopeSelectorCardComponent<any>;
    let fixture: ComponentFixture<ScopeSelectorCardComponent<any>>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [RadioInputComponent, ScopeSelectorCardComponent],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(ScopeSelectorCardComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
