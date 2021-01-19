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
import {Tracker} from '../../../../core/creatives/types/tracker';
import {
    TRACKER_EVENT_TYPE_NAMES,
    TRACKER_EVENT_TYPE_OPTIONS,
    TRACKER_METHOD_EVENT_TYPES,
    TRACKER_METHOD_OPTIONS,
} from '../../content-ad.config';
import {
    TrackerEventType,
    TrackerMethod,
} from '../../../../core/creatives/creatives.constants';
import {ContentAdTrackerErrors} from '../../types/content-ad-tracker-errors';
import {ChangeEvent} from '../../../../shared/types/change-event';

@Component({
    selector: 'zem-content-ad-tracker-form',
    templateUrl: './content-ad-tracker-form.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ContentAdTrackerFormComponent implements OnChanges {
    @Input()
    contentAdTracker: Tracker;
    @Input()
    contentAdTrackerErrors: ContentAdTrackerErrors;
    @Input()
    isDisabled: boolean = false;
    @Output()
    contentAdTrackerChange: EventEmitter<
        ChangeEvent<Tracker>
    > = new EventEmitter<ChangeEvent<Tracker>>();

    allTrackerEventTypes = TRACKER_EVENT_TYPE_OPTIONS;
    availableTrackerEventTypes: {
        value: TrackerEventType;
        name: string;
    }[] = [];
    trackerEventTypeNames = TRACKER_EVENT_TYPE_NAMES;
    availableTrackerMethods = TRACKER_METHOD_OPTIONS;

    trackerMethod = TrackerMethod;

    showFallbackUrlInput: boolean = false;
    showMacroFormatWarning: boolean = false;

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.contentAdTracker && this.contentAdTracker.fallbackUrl) {
            this.showFallbackUrlInput = true;
        }

        if (changes.contentAdTracker && this.contentAdTracker.url) {
            this.showMacroFormatWarning = this.contentAdTracker.url.includes(
                '${'
            );
        }

        if (changes.contentAdTracker && this.contentAdTracker.method) {
            this.availableTrackerEventTypes = this.getAvailableTrackerEventTypes(
                this.contentAdTracker.method,
                this.allTrackerEventTypes,
                TRACKER_METHOD_EVENT_TYPES
            );
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
                eventType:
                    method === TrackerMethod.JS
                        ? TrackerEventType.IMPRESSION
                        : this.contentAdTracker.eventType,
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

    private getAvailableTrackerEventTypes(
        method: TrackerMethod,
        allTrackerEventTypes: {
            value: TrackerEventType;
            name: string;
        }[],
        methodEventTypes: {
            [key in TrackerMethod]: TrackerEventType[];
        }
    ) {
        return allTrackerEventTypes.filter(eventType => {
            return methodEventTypes[method].includes(eventType.value);
        });
    }
}
