import './bid-modifier-upload-modal.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    OnInit,
} from '@angular/core';
import {Breakdown} from '../../../../../app.constants';
import {BidModifierUploadModalStore} from './services/bid-modifier-upload-modal.store';
import {APP_CONFIG} from '../../../../../app.config';

@Component({
    selector: 'zem-bid-modifier-upload-modal',
    templateUrl: './bid-modifier-upload-modal.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [BidModifierUploadModalStore],
})
export class BidModifierUploadModalComponent implements OnInit {
    @Input()
    adGroupId: number;
    @Input()
    breakdown: Breakdown;
    @Output()
    importSuccess = new EventEmitter<void>();
    @Output()
    cancel = new EventEmitter<void>();

    Breakdown = Breakdown;

    constructor(public store: BidModifierUploadModalStore) {}

    ngOnInit(): void {
        this.store.init(this.adGroupId, this.breakdown);
    }

    downloadErrors(): void {
        const url = `${APP_CONFIG.apiRestInternalUrl}/adgroups/${
            this.adGroupId
        }/bidmodifiers/error_download/${
            this.store.state.fieldsErrors.errorFileUrl
        }/`;
        window.open(url, '_blank');
    }

    downloadExample(): void {
        const url = `${
            APP_CONFIG.apiRestInternalUrl
        }/adgroups/bidmodifiers/example_csv_download/${
            this.store.state.breakdown
        }/`;
        window.open(url, '_blank');
    }

    import(): void {
        this.store.import().then(() => {
            this.importSuccess.emit();
        });
    }

    onFilesChange($event: File[]): void {
        const file: File = $event.length > 0 ? $event[0] : null;
        this.store.updateFile(file);
    }
}
