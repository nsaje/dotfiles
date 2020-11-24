import './content-ad-tracker-form.component.less';
import {
    Input,
    Output,
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import {ContentAdTracker} from '../../types/content-ad-tracker';
import {
    TRACKER_EVENT_TYPE_NAMES,
    TRACKER_EVENT_TYPE_OPTIONS,
    TRACKER_METHOD_OPTIONS,
} from '../../content-ad.config';
import {TrackerEventType, TrackerMethod} from '../../content-ad.constants';
import {ContentAdTrackerErrors} from '../../types/content-ad-tracker-errors';
import {ChangeEvent} from '../../../../shared/types/change-event';

@Component({
    selector: 'zem-content-ad-tracker-form',
    templateUrl: './content-ad-tracker-form.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ContentAdTrackerFormComponent implements OnChanges {
    @Input()
    contentAdTracker: ContentAdTracker;
    @Input()
    contentAdTrackerErrors: ContentAdTrackerErrors;
    @Input()
    isDisabled: boolean = false;
    @Output()
    contentAdTrackerChange: EventEmitter<
        ChangeEvent<ContentAdTracker>
    > = new EventEmitter<ChangeEvent<ContentAdTracker>>();

    availableTrackerEventTypes = TRACKER_EVENT_TYPE_OPTIONS;
    availableTrackerMethods = TRACKER_METHOD_OPTIONS;
    trackerEventTypeNames = TRACKER_EVENT_TYPE_NAMES;
    trackerMethod = TrackerMethod;

    showFallbackUrlInput: boolean = false;

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.contentAdTracker && this.contentAdTracker.fallbackUrl) {
            this.showFallbackUrlInput = true;
        }
    }

    onEventTypeChanged(eventType: TrackerEventType): void {
        this.contentAdTrackerChange.emit({
            target: this.contentAdTracker,
            changes: {
                eventType: eventType,
            },
        });
    }

    onMethodChanged(method: TrackerMethod): void {
        this.contentAdTrackerChange.emit({
            target: this.contentAdTracker,
            changes: {
                method: method,
            },
        });
    }

    onUrlChanged(url: string): void {
        this.contentAdTrackerChange.emit({
            target: this.contentAdTracker,
            changes: {
                url: url,
            },
        });
    }

    onFallbackUrlChanged(fallbackUrl: string): void {
        this.contentAdTrackerChange.emit({
            target: this.contentAdTracker,
            changes: {
                fallbackUrl: fallbackUrl,
            },
        });
    }

    onTrackerOptionalChanged(trackerOptional: boolean): void {
        this.contentAdTrackerChange.emit({
            target: this.contentAdTracker,
            changes: {
                trackerOptional: trackerOptional,
            },
        });
    }
}