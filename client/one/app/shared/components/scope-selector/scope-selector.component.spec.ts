import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {ScopeSelectorCardComponent} from './components/scope-selector-card.component';
import {ScopeSelectorComponent} from './scope-selector.component';
import {RadioInputComponent} from '../radio-input/radio-input.component';

describe('ScopeSelectorComponent', () => {
    let component: ScopeSelectorComponent;
    let fixture: ComponentFixture<ScopeSelectorComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                RadioInputComponent,
                ScopeSelectorCardComponent,
                ScopeSelectorComponent,
            ],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(ScopeSelectorComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
