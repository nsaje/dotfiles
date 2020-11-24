import './content-ad-tracker.component.less';
import {
    Input,
    Output,
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    OnChanges,
    OnInit,
} from '@angular/core';
import {ContentAdTracker} from '../../types/content-ad-tracker';
import {TRACKER_EVENT_TYPE_NAMES} from '../../content-ad.config';
import {ContentAdTrackerErrors} from '../../types/content-ad-tracker-errors';

@Component({
    selector: 'zem-content-ad-tracker',
    templateUrl: './content-ad-tracker.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ContentAdTrackerComponent implements OnChanges {
    @Input()
    contentAdTracker: ContentAdTracker;
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
        if (this.contentAdTrackerErrors || !this.contentAdTracker?.url) {
            this.isEditFormVisible = true;
        }
    }
}
