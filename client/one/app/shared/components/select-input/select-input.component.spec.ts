import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {NgSelectModule} from '@ng-select/ng-select';
import {SelectInputComponent} from './select-input.component';
import {FocusDirective} from '../../directives/focus.directive';

describe('SelectInputComponent', () => {
    let component: SelectInputComponent;
    let fixture: ComponentFixture<SelectInputComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [SelectInputComponent, FocusDirective],
            imports: [FormsModule, NgSelectModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(SelectInputComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        component.ngOnInit();
        expect(component).toBeDefined();
    });

    it('should correctly emit model on change event', () => {
        component.ngOnInit();

        spyOn(component.valueChange, 'emit').and.stub();

        component.onChange({value: 'TEST'});
        expect(component.valueChange.emit).toHaveBeenCalledWith('TEST');
        (<any>component.valueChange.emit).calls.reset();

        component.onChange(undefined);
        expect(component.valueChange.emit).toHaveBeenCalledWith(null);
        (<any>component.valueChange.emit).calls.reset();

        component.onChange(null);
        expect(component.valueChange.emit).toHaveBeenCalledWith(null);
    });
});
