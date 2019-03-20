import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SimpleChange} from '@angular/core';
import {RadioInputComponent} from './radio-input.component';

describe('RadioInputComponent', () => {
    let component: RadioInputComponent;
    let fixture: ComponentFixture<RadioInputComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [RadioInputComponent],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(RadioInputComponent);
        component = fixture.componentInstance;
    });

    it('should correctly determine if radio button is checked on inputs changes', () => {
        const mockedGroupModel = 'test';
        let mockedValue = 'whatever';
        component.groupModel = mockedGroupModel;
        component.value = mockedValue;
        component.ngOnChanges({
            groupModel: new SimpleChange(null, mockedGroupModel, false),
        });
        expect(component.isChecked).toBe(false);

        mockedValue = 'test';
        component.value = mockedValue;
        component.ngOnChanges({
            value: new SimpleChange(null, mockedValue, false),
        });
        expect(component.isChecked).toBe(true);
    });
});
