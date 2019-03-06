import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {BidModifierInputComponent} from './bid-modifier-input.component';
import {SimpleChange} from '@angular/core';
import {PrefixedInputComponent} from '../prefixed-input/prefixed-input.component';
import {DecimalInputComponent} from '../decimal-input/decimal-input.component';
import {FilterKeydownEventDirective} from '../../directives/filter-keydown-event.directive';
import {FocusDirective} from '../../directives/focus.directive';

describe('BidModifierInputComponent', () => {
    let component: BidModifierInputComponent;
    let fixture: ComponentFixture<BidModifierInputComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                PrefixedInputComponent,
                DecimalInputComponent,
                BidModifierInputComponent,
                FilterKeydownEventDirective,
                FocusDirective,
            ],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(BidModifierInputComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should correctly emit model on addDeltaPercent event', () => {
        spyOn(component.valueChange, 'emit').and.stub();

        const value = '0.00';
        component.value = value;
        component.ngOnChanges({
            value: new SimpleChange(null, value, false),
        });
        expect(component.model).toEqual('0.00');

        component.addDeltaPercent(-1);
        expect(component.valueChange.emit).toHaveBeenCalledWith('-1.00');
    });

    it('should correctly emit model on addDeltaPercent event', () => {
        spyOn(component.valueChange, 'emit').and.stub();

        const value = '0.00';
        component.value = value;
        component.ngOnChanges({
            value: new SimpleChange(null, value, false),
        });
        expect(component.model).toEqual('0.00');

        component.addDeltaPercent(1);
        expect(component.valueChange.emit).toHaveBeenCalledWith('1.00');
    });
});
