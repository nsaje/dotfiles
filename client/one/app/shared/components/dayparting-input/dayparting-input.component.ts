import './dayparting-input.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Output,
    EventEmitter,
    Input,
    SimpleChanges,
    OnChanges,
    HostListener,
} from '@angular/core';
import * as clone from 'clone';
import {DaypartingDay} from './dayparting-day';

@Component({
    selector: 'zem-dayparting-input',
    templateUrl: './dayparting-input.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DaypartingInputComponent implements OnChanges {
    @Input('dayparting')
    originalDayparting: DaypartingDay[];
    @Input()
    isDisabled: boolean;
    @Output()
    onSelection = new EventEmitter<DaypartingDay[]>();

    dayparting: DaypartingDay[];
    isSelecting = false;
    stateToApply = false;
    selectionStartDayIndex: number;
    selectionStartHour: number;
    selectionPreviousDayIndex: number;
    selectionPreviousHour: number;

    ngOnChanges(changes: SimpleChanges) {
        if (changes.originalDayparting) {
            this.dayparting = clone(this.originalDayparting);
        }
    }

    startSelection(day: DaypartingDay, hour: number): boolean {
        if (!this.isDisabled && !this.isSelecting) {
            this.isSelecting = true;
            this.stateToApply = !day.hours[hour];

            const dayIndex = this.dayparting.indexOf(day);
            this.selectionStartDayIndex = this.selectionPreviousDayIndex = dayIndex;
            this.selectionStartHour = this.selectionPreviousHour = hour;

            this.toggleMultipleHourStates(day, hour);
            return false;
        }
    }

    @HostListener('document:mouseup')
    stopSelection() {
        if (this.isSelecting) {
            this.isSelecting = false;
            this.onSelection.emit(this.dayparting);
        }
    }

    toggleMultipleHourStates(toDay: DaypartingDay, toHour: number): boolean {
        if (this.isSelecting) {
            let updatedDayparting = clone(this.dayparting);

            // Disable previously selected days and hours
            updatedDayparting = this.applySelection(
                updatedDayparting,
                false,
                this.selectionStartDayIndex,
                this.selectionPreviousDayIndex,
                this.selectionStartHour,
                this.selectionPreviousHour
            );

            const toDayIndex = this.dayparting.indexOf(toDay);
            this.selectionPreviousDayIndex = toDayIndex;
            this.selectionPreviousHour = toHour;

            // Toggle newly selected days and hours
            updatedDayparting = this.applySelection(
                updatedDayparting,
                this.stateToApply,
                this.selectionStartDayIndex,
                toDayIndex,
                this.selectionStartHour,
                toHour
            );

            this.dayparting = updatedDayparting;
        }

        return false;
    }

    toggleHourState(day: DaypartingDay, hour: number): boolean {
        day.hours[hour] = !day.hours[hour];
        this.onSelection.emit(this.dayparting);
        return false;
    }

    trackByIndex(index: number): number {
        return index;
    }

    private applySelection(
        dayparting: DaypartingDay[],
        stateToApply: boolean,
        startDayIndex: number,
        toDayIndex: number,
        startHour: number,
        toHour: number
    ): DaypartingDay[] {
        const dayMin = Math.min(startDayIndex, toDayIndex);
        const dayMax = Math.max(startDayIndex, toDayIndex);
        const hourMin = Math.min(startHour, toHour);
        const hourMax = Math.max(startHour, toHour);
        for (let dayIndex = dayMin; dayIndex <= dayMax; dayIndex++) {
            for (let hour = hourMin; hour <= hourMax; hour++) {
                dayparting[dayIndex].hours[hour] = stateToApply;
            }
        }
        return dayparting;
    }
}
