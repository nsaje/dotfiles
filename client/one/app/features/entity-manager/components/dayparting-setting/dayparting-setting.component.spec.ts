import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SimpleChange} from '@angular/core';

import {DaypartingSettingComponent} from './dayparting-setting.component';
import {DaypartingInputComponent} from '../../../../shared/components/dayparting-input/dayparting-input.component';
import {Day} from '../../../../app.constants';
import {DaypartingSetting} from '../../types/dayparting-setting';
import {DaypartingDay} from '../../../../shared/components/dayparting-input/dayparting-day';

describe('DaypartingSettingComponent', () => {
    let component: DaypartingSettingComponent;
    let fixture: ComponentFixture<DaypartingSettingComponent>;
    let mockedSetting: DaypartingSetting;
    let mockedDayparting: DaypartingDay[];

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                DaypartingSettingComponent,
                DaypartingInputComponent,
            ],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DaypartingSettingComponent);
        component = fixture.componentInstance;

        mockedSetting = {
            [Day.Monday]: [0, 1],
            [Day.Tuesday]: [2, 3],
            [Day.Wednesday]: [4, 5],
            [Day.Thursday]: [6, 7],
            [Day.Friday]: [8, 9],
            [Day.Saturday]: [10, 11],
        };
        mockedDayparting = [
            {
                day: Day.Monday,
                name: 'Monday',
                hours: [true, true, ...Array(22).fill(false)],
            },
            {
                day: Day.Tuesday,
                name: 'Tuesday',
                hours: [
                    ...Array(2).fill(false),
                    true,
                    true,
                    ...Array(20).fill(false),
                ],
            },
            {
                day: Day.Wednesday,
                name: 'Wednesday',
                hours: [
                    ...Array(4).fill(false),
                    true,
                    true,
                    ...Array(18).fill(false),
                ],
            },
            {
                day: Day.Thursday,
                name: 'Thursday',
                hours: [
                    ...Array(6).fill(false),
                    true,
                    true,
                    ...Array(16).fill(false),
                ],
            },
            {
                day: Day.Friday,
                name: 'Friday',
                hours: [
                    ...Array(8).fill(false),
                    true,
                    true,
                    ...Array(14).fill(false),
                ],
            },
            {
                day: Day.Saturday,
                name: 'Saturday',
                hours: [
                    ...Array(10).fill(false),
                    true,
                    true,
                    ...Array(12).fill(false),
                ],
            },
            {
                day: Day.Sunday,
                name: 'Sunday',
                hours: Array(24).fill(false),
            },
        ];
    });

    it('should correctly generate dayparting on empty dayparting setting input', () => {
        const mockedSetting: DaypartingSetting = {};
        component.daypartingSetting = mockedSetting;
        component.ngOnChanges({
            daypartingSetting: new SimpleChange(null, mockedSetting, false),
        });
        component.dayparting.forEach(day => {
            expect(day.hours).toEqual(Array(24).fill(false));
        });
    });

    it('should correctly generate dayparting on dayparting setting input change', () => {
        component.daypartingSetting = mockedSetting;
        component.ngOnChanges({
            daypartingSetting: new SimpleChange(null, mockedSetting, false),
        });
        expect(component.dayparting).toEqual(mockedDayparting);
    });

    it('should set timezone on dayparting setting input change', () => {
        let mockedSetting: DaypartingSetting = {};
        component.daypartingSetting = mockedSetting;
        component.ngOnChanges({
            daypartingSetting: new SimpleChange(null, mockedSetting, false),
        });
        expect(component.timezone).toBe(undefined);

        mockedSetting = {timezone: 'UTC'};
        component.daypartingSetting = mockedSetting;
        component.ngOnChanges({
            daypartingSetting: new SimpleChange(null, mockedSetting, false),
        });
        expect(component.timezone).toBe('UTC');
    });

    it('should correctly determine if dayparting settings widget is visible', () => {
        let mockedSetting: DaypartingSetting = {};
        component.daypartingSetting = mockedSetting;
        component.ngOnChanges({
            daypartingSetting: new SimpleChange(null, mockedSetting, false),
        });
        expect(component.areDaypartingSettingsVisible).toBe(false);

        component.enableDaypartingSettings();
        expect(component.areDaypartingSettingsVisible).toBe(true);

        component.wereDaypartingSettingsEnabled = false;
        mockedSetting = {[Day.Monday]: [0, 1]};
        component.daypartingSetting = mockedSetting;
        component.ngOnChanges({
            daypartingSetting: new SimpleChange(null, mockedSetting, false),
        });
        expect(component.areDaypartingSettingsVisible).toBe(true);
    });

    it('should correctly generate dayparting setting on dayparting selection update', () => {
        spyOn(component.onChange, 'emit').and.stub();
        component.timezone = 'UTC';
        component.handleDaypartingSelectionUpdate(mockedDayparting);
        expect(component.onChange.emit).toHaveBeenCalledWith({
            ...mockedSetting,
            timezone: 'UTC',
        });
    });
});
