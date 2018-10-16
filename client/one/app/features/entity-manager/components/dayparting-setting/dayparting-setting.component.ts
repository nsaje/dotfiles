import './dayparting-setting.component.less';

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
import {downgradeComponent} from '@angular/upgrade/static';
import {Day} from '../../../../app.constants';
import {DaypartingSetting} from '../../types/dayparting-setting';
import {DaypartingDay} from '../../../../shared/components/dayparting-input/dayparting-day';

@Component({
    selector: 'zem-dayparting-setting',
    templateUrl: './dayparting-setting.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DaypartingSettingComponent implements OnChanges {
    @Input()
    daypartingSetting: DaypartingSetting;
    @Input()
    errors: any;
    @Output()
    onChange = new EventEmitter<DaypartingSetting>();

    wereDaypartingSettingsEnabled = false;
    areDaypartingSettingsVisible = false;
    dayparting: DaypartingDay[];
    timezone: string;

    ngOnChanges(changes: SimpleChanges) {
        if (changes.daypartingSetting) {
            this.dayparting = this.generateDaypartingFromSettings(
                this.daypartingSetting
            );
            this.timezone = (this.daypartingSetting || {}).timezone;
            this.areDaypartingSettingsVisible = this.getDaypartingSettingsVisibility(
                this.wereDaypartingSettingsEnabled,
                this.daypartingSetting
            );
        }
    }

    handleDaypartingSelectionUpdate(dayparting: DaypartingDay[]) {
        this.onChange.emit(this.generateSettings(dayparting, this.timezone));
    }

    enableDaypartingSettings() {
        this.wereDaypartingSettingsEnabled = this.areDaypartingSettingsVisible = true;
    }

    private getDaypartingSettingsVisibility(
        wereDaypartingSettingsEnabled: boolean,
        daypartingSetting: DaypartingSetting
    ): boolean {
        return (
            wereDaypartingSettingsEnabled ||
            (daypartingSetting && Object.keys(daypartingSetting).length !== 0)
        );
    }

    private generateDaypartingFromSettings(
        daypartingSetting: DaypartingSetting = {}
    ): DaypartingDay[] {
        return [
            {
                day: Day.Monday,
                name: 'Monday',
                hours: this.generateHoursList(daypartingSetting[Day.Monday]),
            },
            {
                day: Day.Tuesday,
                name: 'Tuesday',
                hours: this.generateHoursList(daypartingSetting[Day.Tuesday]),
            },
            {
                day: Day.Wednesday,
                name: 'Wednesday',
                hours: this.generateHoursList(daypartingSetting[Day.Wednesday]),
            },
            {
                day: Day.Thursday,
                name: 'Thursday',
                hours: this.generateHoursList(daypartingSetting[Day.Thursday]),
            },
            {
                day: Day.Friday,
                name: 'Friday',
                hours: this.generateHoursList(daypartingSetting[Day.Friday]),
            },
            {
                day: Day.Saturday,
                name: 'Saturday',
                hours: this.generateHoursList(daypartingSetting[Day.Saturday]),
            },
            {
                day: Day.Sunday,
                name: 'Sunday',
                hours: this.generateHoursList(daypartingSetting[Day.Sunday]),
            },
        ];
    }

    private generateHoursList(activeHours: number[] = []): boolean[] {
        const hours = [];
        for (let i = 0; i < 24; i++) {
            hours[i] = activeHours.indexOf(i) !== -1;
        }
        return hours;
    }

    private generateSettings(
        dayparting: DaypartingDay[],
        timezone: string
    ): DaypartingSetting {
        const daypartingSetting: DaypartingSetting = {};

        if (timezone) {
            daypartingSetting.timezone = timezone;
        }

        dayparting.forEach(day => {
            const activeHours = this.getDayActiveHours(day);
            if (activeHours.length > 0) {
                daypartingSetting[day.day] = activeHours;
            }
        });

        return daypartingSetting;
    }

    private getDayActiveHours(day: DaypartingDay): number[] {
        const activeHours: number[] = [];
        day.hours.forEach((isActive, hour) => {
            if (isActive) {
                activeHours.push(hour);
            }
        });
        return activeHours;
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemDaypartingSetting',
    downgradeComponent({
        component: DaypartingSettingComponent,
        inputs: ['daypartingSetting', 'errors'],
    })
);
