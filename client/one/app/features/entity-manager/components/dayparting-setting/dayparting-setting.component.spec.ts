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

    it('should generate dayparting on dayparting setting input change', () => {
        component.daypartingSetting = mockedSetting;
        component.ngOnChanges({
            daypartingSetting: new SimpleChange(null, mockedSetting, false),
        });
        expect(component.dayparting).toEqual(mockedDayparting);
    });

    it('should generate dayparting with all hours active if dayparting setting is empty', () => {
        const mockedSetting: DaypartingSetting = {};
        component.daypartingSetting = mockedSetting;
        component.ngOnChanges({
            daypartingSetting: new SimpleChange(null, mockedSetting, false),
        });
        expect(component.timezone).not.toBeDefined();
        expect(component.dayparting).toBeDefined();
        component.dayparting.forEach(day => {
            expect(day.hours).toEqual(Array(24).fill(true));
        });
    });

    it('should set timezone on dayparting setting input change', () => {
        let mockedSetting: DaypartingSetting = {};
        component.daypartingSetting = mockedSetting;
        component.ngOnChanges({
            daypartingSetting: new SimpleChange(null, mockedSetting, false),
        });
        expect(component.timezone).not.toBeDefined();

        mockedSetting = {timezone: 'UTC'};
        component.daypartingSetting = mockedSetting;
        component.ngOnChanges({
            daypartingSetting: new SimpleChange(null, mockedSetting, false),
        });
        expect(component.timezone).toBe('UTC');
    });

    it('should correctly generate dayparting setting on dayparting selection update', () => {
        spyOn(component.valueChange, 'emit').and.stub();
        component.timezone = 'UTC';
        component.handleDaypartingSelectionUpdate(mockedDayparting);
        expect(component.valueChange.emit).toHaveBeenCalledWith({
            ...mockedSetting,
            timezone: 'UTC',
        });
    });

    it('should return empty dayparting setting on dayparting selection update when every hour of every day is active', () => {
        spyOn(component.valueChange, 'emit').and.stub();
        component.timezone = 'UTC';
        const allActiveDayparting = Array(7).fill({
            hours: Array(24).fill(true),
        });
        component.handleDaypartingSelectionUpdate(allActiveDayparting);
        expect(component.valueChange.emit).toHaveBeenCalledWith({});
    });
});
