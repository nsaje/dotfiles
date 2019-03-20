import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SimpleChange} from '@angular/core';
import {SharedModule} from '../../../../shared/shared.module';
import {DateSettingComponent} from './date-setting.component';

describe('DateSettingComponent', () => {
    let component: DateSettingComponent;
    let fixture: ComponentFixture<DateSettingComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [DateSettingComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DateSettingComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized when value input is defined', () => {
        const mockedDate = new Date();
        component.value = mockedDate;
        component.ngOnChanges({
            value: new SimpleChange(null, mockedDate, false),
        });
        expect(component.model).toEqual(mockedDate);
        expect(component.lastNonNullValue).toEqual(mockedDate);
        expect(component.isManualOverrideEnabled).toBe(false);
    });

    it('should be correctly initialized when value input is defined', () => {
        const mockedDate: Date = null;
        component.value = mockedDate;
        component.ngOnChanges({
            value: new SimpleChange(null, mockedDate, false),
        });
        expect(component.model).toEqual(null);
        expect(component.lastNonNullValue).toBe(undefined);
        expect(component.isManualOverrideEnabled).toBe(true);
    });

    it('should emit null in valueChange output when manual override is toggled on', () => {
        spyOn(component.valueChange, 'emit').and.stub();
        component.onManualOverrideToggle(true);
        expect(component.valueChange.emit).toHaveBeenCalledWith(null);
    });

    it('should emit last selected date in valueChange output when manual override is toggled off', () => {
        spyOn(component.valueChange, 'emit').and.stub();
        const mockedDate = new Date();
        component.lastNonNullValue = mockedDate;
        component.onManualOverrideToggle(false);
        expect(component.valueChange.emit).toHaveBeenCalledWith(mockedDate);
    });

    it('should emit min date in valueChange output when manual override is toggled off and last selected date is not available', () => {
        spyOn(component.valueChange, 'emit').and.stub();
        const mockedDate = new Date();
        component.minDate = mockedDate;
        component.onManualOverrideToggle(false);
        expect(component.valueChange.emit).toHaveBeenCalledWith(mockedDate);
    });
});
