import './dayparting-setting.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Output,
    EventEmitter,
    Input,
    SimpleChanges,
    OnChanges,
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

    isDaypartingInputVisible: boolean;
    dayparting: DaypartingDay[];
    timezone: string;

    ngOnChanges(changes: SimpleChanges) {
        if (changes.daypartingSetting) {
            if (this.isDaypartingEnabled(this.daypartingSetting)) {
                this.timezone = this.daypartingSetting.timezone;
                this.dayparting = this.generateDaypartingFromSettings(
                    this.daypartingSetting
                );
                this.isDaypartingInputVisible = true;
            } else {
                this.isDaypartingInputVisible = false;
            }
        }
    }

    handleDaypartingSelectionUpdate(dayparting: DaypartingDay[]) {
        this.onChange.emit(this.generateSettings(dayparting, this.timezone));
    }

    enableDayparting() {
        // Dayparting was previously disabled. When enabling, generate
        // dayparting with all hours active since we want to show every hour in
        // dayparting input as active.
        this.dayparting = this.generateDaypartingFromSettings(
            this.daypartingSetting || {},
            true
        );
        this.isDaypartingInputVisible = true;
    }

    private isDaypartingEnabled(daypartingSetting: DaypartingSetting): boolean {
        return daypartingSetting && Object.keys(daypartingSetting).length !== 0;
    }

    private generateDaypartingFromSettings(
        daypartingSetting: DaypartingSetting,
        allActive = false
    ): DaypartingDay[] {
        return [
            {
                day: Day.Monday,
                name: 'Monday',
                hours: this.generateHoursList(
                    allActive,
                    daypartingSetting[Day.Monday]
                ),
            },
            {
                day: Day.Tuesday,
                name: 'Tuesday',
                hours: this.generateHoursList(
                    allActive,
                    daypartingSetting[Day.Tuesday]
                ),
            },
            {
                day: Day.Wednesday,
                name: 'Wednesday',
                hours: this.generateHoursList(
                    allActive,
                    daypartingSetting[Day.Wednesday]
                ),
            },
            {
                day: Day.Thursday,
                name: 'Thursday',
                hours: this.generateHoursList(
                    allActive,
                    daypartingSetting[Day.Thursday]
                ),
            },
            {
                day: Day.Friday,
                name: 'Friday',
                hours: this.generateHoursList(
                    allActive,
                    daypartingSetting[Day.Friday]
                ),
            },
            {
                day: Day.Saturday,
                name: 'Saturday',
                hours: this.generateHoursList(
                    allActive,
                    daypartingSetting[Day.Saturday]
                ),
            },
            {
                day: Day.Sunday,
                name: 'Sunday',
                hours: this.generateHoursList(
                    allActive,
                    daypartingSetting[Day.Sunday]
                ),
            },
        ];
    }

    private generateHoursList(
        allActive: boolean,
        activeHours: number[] = []
    ): boolean[] {
        if (allActive) {
            return new Array<boolean>(24).fill(true);
        }
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

        let allActive = true;
        dayparting.forEach(day => {
            const activeHours = this.getDayActiveHours(day);
            if (activeHours.length > 0) {
                daypartingSetting[day.day] = activeHours;
            }
            if (activeHours.length < 24) {
                allActive = false;
            }
        });

        // If every hour of every day is active, disable dayparting since ads
        // will run all the time.
        if (allActive) {
            return {};
        }
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
