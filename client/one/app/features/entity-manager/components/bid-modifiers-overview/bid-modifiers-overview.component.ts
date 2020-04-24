import './bid-modifiers-overview.component.less';

import {APP_CONFIG} from '../../../../app.config';
import {
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    Input,
    Output,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import {BidModifierTypeSummary} from '../../../../core/bid-modifiers/types/bid-modifier-type-summary';
import {BidModifiersImportErrorState} from '../../services/ad-group-settings-store/bid-modifiers-import-error-state';
import {BidModifierUploadSummary} from '../../../../core/bid-modifiers/types/bid-modifier-upload-summary';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {BidModifiersOverviewStore} from './bid-modifiers-overview.store';

@Component({
    selector: 'zem-bid-modifiers-overview',
    templateUrl: './bid-modifiers-overview.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [BidModifiersOverviewStore],
})
export class BidModifiersOverviewComponent implements OnChanges {
    @Input()
    adGroupId: String;
    @Input()
    bidModifierTypeSummaries: BidModifierTypeSummary[];
    @Input()
    importError: BidModifiersImportErrorState;
    @Input()
    importSummary: BidModifierUploadSummary;
    @Output()
    importFileChange = new EventEmitter<File>();

    constructor(public store: BidModifiersOverviewStore) {}

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.bidModifierTypeSummaries) {
            this.store.updateTypeSummaryGridRows(this.bidModifierTypeSummaries);
        }
    }

    exportBidModifiers(): void {
        if (!commonHelpers.isDefined(this.adGroupId)) {
            return;
        }
        const url = `${APP_CONFIG.apiRestInternalUrl}/adgroups/${this.adGroupId}/bidmodifiers/download/`;
        window.open(url, '_blank');
    }

    downloadCsvSampleFile(): void {
        if (!commonHelpers.isDefined(this.adGroupId)) {
            return;
        }
        const url = `${APP_CONFIG.apiRestInternalUrl}/adgroups/bidmodifiers/example_csv_download/`;
        window.open(url, '_blank');
    }

    downloadErrorsFile(): void {
        if (!commonHelpers.isDefined(this.importError)) {
            return;
        }
        const url = commonHelpers.isDefined(this.adGroupId)
            ? `${APP_CONFIG.apiRestInternalUrl}/adgroups/${this.adGroupId}/bidmodifiers/error_download/${this.importError.errorFileUrl}/`
            : `${APP_CONFIG.apiRestInternalUrl}/adgroups/bidmodifiers/error_download/${this.importError.errorFileUrl}/`;
        window.open(url, '_blank');
    }

    onFilesChange($event: File[]): void {
        const file: File = $event.length > 0 ? $event[0] : null;
        this.importFileChange.emit(file);
    }
}
