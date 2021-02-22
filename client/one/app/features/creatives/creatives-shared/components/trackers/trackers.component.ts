import './trackers.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    OnChanges,
    SimpleChanges,
    Output,
    EventEmitter,
    OnInit,
} from '@angular/core';
import * as commonHelpers from '../../../../../shared/helpers/common.helpers';
import {Tracker} from '../../../../../core/creatives/types/tracker';
import {TrackerErrors} from '../../types/tracker-errors';
import {downgradeComponent} from '@angular/upgrade/static';
import {
    MAX_TRACKERS_EXTRA_LIMIT,
    MAX_TRACKERS_LIMIT,
} from '../../creatives-shared.config';
import * as clone from 'clone';
import {ChangeEvent} from '../../../../../shared/types/change-event';

@Component({
    selector: 'zem-trackers',
    templateUrl: './trackers.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TrackersComponent implements OnInit, OnChanges {
    @Input()
    trackers: Tracker[];
    @Input()
    trackersErrors: TrackerErrors[];
    @Input()
    isDisabled: boolean;
    @Input()
    isLoading: boolean = false;
    @Input()
    canUseExtraTrackers: boolean = false;
    @Output()
    trackersChange: EventEmitter<Tracker[]> = new EventEmitter<Tracker[]>();

    maxTrackersLimit: number = MAX_TRACKERS_LIMIT;
    formattedTrackers: Tracker[] = [];
    hasErrors: boolean[] = [];

    ngOnInit() {
        this.maxTrackersLimit = this.canUseExtraTrackers
            ? MAX_TRACKERS_EXTRA_LIMIT
            : MAX_TRACKERS_LIMIT;
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.trackers) {
            this.formattedTrackers = clone(this.trackers);
        }

        if (changes.trackersErrors) {
            this.hasErrors = this.checkForErrors(this.trackersErrors);
        }
    }

    trackByIndex(index: number): string {
        return index.toString();
    }

    onTrackerChange(changeEvent: ChangeEvent<Tracker>, index: number): void {
        const previousTrackerState = clone(this.formattedTrackers[index]);

        this.formattedTrackers[index] = {
            ...this.formattedTrackers[index],
            ...changeEvent.changes,
        };

        if (
            (commonHelpers.isDefined(previousTrackerState.eventType) &&
                commonHelpers.isDefined(previousTrackerState.method)) ||
            commonHelpers.isDefined(this.formattedTrackers[index].url)
        ) {
            this.trackersChange.emit(this.formattedTrackers);
        }
    }

    onTrackerRemove(index: number): void {
        this.formattedTrackers.splice(index, 1);
        this.trackersChange.emit(this.formattedTrackers);
    }

    addTracker(): void {
        this.formattedTrackers.push({
            eventType: null,
            method: null,
            url: null,
            fallbackUrl: null,
            trackerOptional: true,
        });
    }

    checkForErrors(errors: TrackerErrors[]): boolean[] {
        const hasErrors: boolean[] = [];
        if (commonHelpers.isDefined(errors)) {
            errors.forEach(error => {
                hasErrors.push(
                    commonHelpers.isDefined(error) &&
                        Object.values(error).some(e => e)
                );
            });
        }
        return hasErrors;
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemTrackers',
    downgradeComponent({
        component: TrackersComponent,
        propagateDigest: false,
    })
);
