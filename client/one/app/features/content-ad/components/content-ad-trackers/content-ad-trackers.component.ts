import './content-ad-trackers.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    OnChanges,
    SimpleChanges,
    Output,
    EventEmitter,
} from '@angular/core';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {ContentAdTracker} from '../../types/content-ad-tracker';
import {ContentAdTrackerErrors} from '../../types/content-ad-tracker-errors';
import {downgradeComponent} from '@angular/upgrade/static';
import {MAX_TRACKERS_LIMIT} from '../../content-ad.config';
import * as clone from 'clone';
import {ChangeEvent} from '../../../../shared/types/change-event';

@Component({
    selector: 'zem-content-ad-trackers',
    templateUrl: './content-ad-trackers.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ContentAdTrackersComponent implements OnChanges {
    @Input()
    contentAdTrackers: ContentAdTracker[];
    @Input()
    contentAdTrackersErrors: ContentAdTrackerErrors[];
    @Input()
    isDisabled: boolean;
    @Output()
    contentAdTrackersChange: EventEmitter<
        ContentAdTracker[]
    > = new EventEmitter<ContentAdTracker[]>();

    maxTrackersLimit: number = MAX_TRACKERS_LIMIT;
    trackers: ContentAdTracker[] = [];
    hasErrors: boolean[] = [];

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.contentAdTrackers) {
            this.trackers = clone(this.contentAdTrackers);
        }

        if (changes.contentAdTrackersErrors) {
            this.hasErrors = this.checkForErrors(this.contentAdTrackersErrors);
        }
    }

    trackByIndex(index: number): string {
        return index.toString();
    }

    onContentAdTrackerChange(
        changeEvent: ChangeEvent<ContentAdTracker>,
        index: number
    ): void {
        const previousTrackerState = clone(this.trackers[index]);

        this.trackers[index] = {
            ...this.trackers[index],
            ...changeEvent.changes,
        };

        if (
            commonHelpers.isDefined(previousTrackerState.eventType) &&
            commonHelpers.isDefined(previousTrackerState.method)
        ) {
            this.contentAdTrackersChange.emit(this.trackers);
        }
    }

    onContentAdTrackerRemove(index: number): void {
        this.trackers.splice(index, 1);
        this.contentAdTrackersChange.emit(this.trackers);
    }

    addTracker(): void {
        this.trackers.push({
            eventType: null,
            method: null,
            url: null,
            fallbackUrl: null,
            trackerOptional: true,
        });
    }

    checkForErrors(errors: ContentAdTrackerErrors[]): boolean[] {
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
    'zemContentAdTrackers',
    downgradeComponent({
        component: ContentAdTrackersComponent,
        propagateDigest: false,
    })
);
