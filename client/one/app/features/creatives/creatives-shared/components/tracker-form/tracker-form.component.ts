import './tracker-form.component.less';
import {
    Input,
    Output,
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import {Tracker} from '../../../../../core/creatives/types/tracker';
import {
    TRACKER_EVENT_TYPE_NAMES,
    TRACKER_EVENT_TYPE_OPTIONS,
    TRACKER_METHOD_EVENT_TYPES,
    TRACKER_METHOD_OPTIONS,
} from '../../creatives-shared.config';
import {
    TrackerEventType,
    TrackerMethod,
} from '../../../../../core/creatives/creatives.constants';
import {TrackerErrors} from '../../types/tracker-errors';
import {ChangeEvent} from '../../../../../shared/types/change-event';

@Component({
    selector: 'zem-tracker-form',
    templateUrl: './tracker-form.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TrackerFormComponent implements OnChanges {
    @Input()
    tracker: Tracker;
    @Input()
    trackerErrors: TrackerErrors;
    @Input()
    isDisabled: boolean = false;
    @Output()
    trackerChange: EventEmitter<ChangeEvent<Tracker>> = new EventEmitter<
        ChangeEvent<Tracker>
    >();

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
    showGdprWarning: boolean = false;

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.tracker && this.tracker.fallbackUrl) {
            this.showFallbackUrlInput = true;
        }

        if (changes.tracker && this.tracker.url) {
            this.showMacroFormatWarning = this.tracker.url.includes('${');
            this.showGdprWarning = !this.tracker.url.includes('gdpr');
        }

        if (changes.tracker && this.tracker.method) {
            this.availableTrackerEventTypes = this.getAvailableTrackerEventTypes(
                this.tracker.method,
                this.allTrackerEventTypes,
                TRACKER_METHOD_EVENT_TYPES
            );
        }
    }

    onEventTypeChanged(eventType: TrackerEventType): void {
        this.trackerChange.emit({
            target: this.tracker,
            changes: {
                eventType: eventType,
            },
        });
    }

    onMethodChanged(method: TrackerMethod): void {
        this.trackerChange.emit({
            target: this.tracker,
            changes: {
                method: method,
                eventType:
                    method === TrackerMethod.JS
                        ? TrackerEventType.IMPRESSION
                        : this.tracker.eventType,
            },
        });
    }

    onUrlChanged(url: string): void {
        this.trackerChange.emit({
            target: this.tracker,
            changes: {
                url: url,
            },
        });
    }

    onFallbackUrlChanged(fallbackUrl: string): void {
        this.trackerChange.emit({
            target: this.tracker,
            changes: {
                fallbackUrl: fallbackUrl,
            },
        });
    }

    onTrackerOptionalChanged(trackerOptional: boolean): void {
        this.trackerChange.emit({
            target: this.tracker,
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
