import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SimpleChange} from '@angular/core';
import * as clone from 'clone';

import {DaypartingInputComponent} from './dayparting-input.component';
import {Day} from '../../../app.constants';
import {DaypartingDay} from './dayparting-day';

describe('DaypartingInputComponent', () => {
    let component: DaypartingInputComponent;
    let fixture: ComponentFixture<DaypartingInputComponent>;
    let mockedDayparting: DaypartingDay[];

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [DaypartingInputComponent],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DaypartingInputComponent);
        component = fixture.componentInstance;

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

    it('should start selection, set relevant properties and toggle hour state at selection start', () => {
        const mockedDayIndex = 1;
        const mockedHour = 2;
        component.dayparting = clone(mockedDayparting);

        expect(component.dayparting[mockedDayIndex].hours[mockedHour]).toBe(
            true
        );

        component.startSelection(
            component.dayparting[mockedDayIndex],
            mockedHour
        );

        expect(component.isSelecting).toBe(true);
        expect(component.stateToApply).toBe(false);
        expect(component.selectionStartDayIndex).toBe(mockedDayIndex);
        expect(component.selectionStartHour).toBe(mockedHour);
        expect(component.dayparting[mockedDayIndex].hours[mockedHour]).toBe(
            false
        );
    });

    it('should toggle multiple hour states on selection update', () => {
        const mockedDayIndex1 = 1;
        const mockedHour1 = 2;
        const mockedDayIndex2 = 5;
        const mockedHour2 = 17;
        component.dayparting = clone(mockedDayparting);

        component.startSelection(
            component.dayparting[mockedDayIndex1],
            mockedHour1
        );
        component.toggleMultipleHourStates(
            component.dayparting[mockedDayIndex2],
            mockedHour2
        );

        const expectedState = !mockedDayparting[mockedDayIndex1].hours[
            mockedHour1
        ];
        for (let i = mockedDayIndex1; i <= mockedDayIndex2; i++) {
            for (let j = mockedHour1; j <= mockedHour2; j++) {
                expect(component.dayparting[i].hours[j]).toBe(expectedState);
            }
        }
    });

    it('should stop selection and emit new dayparting value', () => {
        spyOn(component.onSelection, 'emit').and.stub();
        component.dayparting = mockedDayparting;
        component.isSelecting = true;
        component.stopSelection();
        expect(component.isSelecting).toBe(false);
        expect(component.onSelection.emit).toHaveBeenCalledWith(
            mockedDayparting
        );
    });

    it('should toggle hour state', () => {
        spyOn(component.onSelection, 'emit').and.stub();
        const day = mockedDayparting[0];
        expect(day.hours[0]).toBe(true);
        component.toggleHourState(day, 0);
        expect(day.hours[0]).toBe(false);
        expect(component.onSelection.emit).toHaveBeenCalled();
    });
});
