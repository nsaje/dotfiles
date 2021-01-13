import './content-ad-tracker.component.less';
import {
    Input,
    Output,
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    OnChanges,
} from '@angular/core';
import {Tracker} from '../../../../core/creatives/types/tracker';
import {TRACKER_EVENT_TYPE_NAMES} from '../../content-ad.config';
import {ContentAdTrackerErrors} from '../../types/content-ad-tracker-errors';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';

@Component({
    selector: 'zem-content-ad-tracker',
    templateUrl: './content-ad-tracker.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ContentAdTrackerComponent implements OnChanges {
    @Input()
    contentAdTracker: Tracker;
    @Input()
    contentAdTrackerErrors: ContentAdTrackerErrors;
    @Input()
    isDisabled: boolean = false;
    @Input()
    index: number;
    @Output()
    contentAdTrackerRemove: EventEmitter<void> = new EventEmitter<void>();

    trackerEventTypeNames = TRACKER_EVENT_TYPE_NAMES;

    isEditFormVisible: boolean = false;

    ngOnChanges(): void {
        if (
            this.hasErrors(this.contentAdTrackerErrors) ||
            !this.contentAdTracker?.url
        ) {
            this.isEditFormVisible = true;
        }
    }

    private hasErrors(contentAdTrackerErrors: ContentAdTrackerErrors) {
        return (
            commonHelpers.isDefined(contentAdTrackerErrors) &&
            Object.values(contentAdTrackerErrors).some(e => e)
        );
    }
}
