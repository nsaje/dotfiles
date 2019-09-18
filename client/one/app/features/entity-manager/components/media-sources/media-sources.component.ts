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
import * as clone from 'clone';

@Component({
    selector: 'zem-media-sources',
    templateUrl: './media-sources.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MediaSourcesComponent implements OnChanges {
    @Input()
    allowedMediaSources: AccountMediaSource[];
    @Input()
    availableMediaSources: AccountMediaSource[];
    @Input()
    allowedMediaSourcesErrors: FieldErrors;
    @Output()
    mediaSourcesAddToAllowed = new EventEmitter<string[]>();
    @Output()
    mediaSourcesRemoveFromAllowed = new EventEmitter<string[]>();

    selectedAvailableMediaSources: string[] = [];
    selectedAllowedMediaSources: string[] = [];

    formattedAvailableMediaSources: AccountMediaSource[] = [];
    formattedAllowedMediaSources: AccountMediaSource[] = [];

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.allowedMediaSources) {
            this.selectedAvailableMediaSources = [];
            this.formattedAvailableMediaSources = clone(
                this.availableMediaSources
            )
                .filter(
                    item =>
                        this.allowedMediaSources
                            .map(x => x.id)
                            .indexOf(item.id) === -1
                )
                .sort((a, b) => {
                    if (a.name < b.name) {
                        return -1;
                    }
                    if (a.name > b.name) {
                        return 1;
                    }
                    return 0;
                });
            this.selectedAllowedMediaSources = [];
            this.formattedAllowedMediaSources = clone(
                this.allowedMediaSources
            ).sort((a, b) => {
                if (a.name < b.name) {
                    return -1;
                }
                if (a.name > b.name) {
                    return 1;
                }
                return 0;
            });
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
