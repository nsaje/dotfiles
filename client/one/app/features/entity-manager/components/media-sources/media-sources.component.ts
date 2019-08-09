import './media-sources.component.less';

import {
    OnChanges,
    SimpleChanges,
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {AccountMediaSource} from '../../../../core/entities/types/account/account-media-source';
import {FieldErrors} from '../../../../shared/types/field-errors';

@Component({
    selector: 'zem-media-sources',
    templateUrl: './media-sources.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MediaSourcesComponent implements OnChanges {
    @Input()
    mediaSources: AccountMediaSource[];
    @Input()
    mediaSourcesErrors: FieldErrors;
    @Output()
    mediaSourcesAddToAllowed = new EventEmitter<string[]>();
    @Output()
    mediaSourcesRemoveFromAllowed = new EventEmitter<string[]>();

    selectedAvailableMediaSources: string[] = [];
    selectedAllowedMediaSources: string[] = [];

    availableMediaSources: AccountMediaSource[] = [];
    allowedMediaSources: AccountMediaSource[] = [];

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.mediaSources) {
            this.selectedAvailableMediaSources = [];
            this.availableMediaSources = this.mediaSources.filter(
                item => !item.allowed
            );
            this.selectedAllowedMediaSources = [];
            this.allowedMediaSources = this.mediaSources.filter(
                item => item.allowed
            );
        }
    }

    addToAllowedMediaSources() {
        this.mediaSourcesAddToAllowed.emit(this.selectedAvailableMediaSources);
    }

    removeFromAllowedMediaSources() {
        this.mediaSourcesRemoveFromAllowed.emit(
            this.selectedAllowedMediaSources
        );
    }

    getMediaSourceText(mediaSource: AccountMediaSource): string {
        let text = mediaSource.name;
        if (!mediaSource.released && mediaSource.deprecated) {
            text += ' (unreleased, deprecated)';
        } else if (!mediaSource.released) {
            text += ' (unreleased)';
        } else if (mediaSource.deprecated) {
            text += ' (deprecated)';
        }

        return text;
    }
}
