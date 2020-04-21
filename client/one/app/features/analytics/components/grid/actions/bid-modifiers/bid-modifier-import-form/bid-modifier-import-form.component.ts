import './bid-modifier-import-form.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    OnInit,
    Output,
    EventEmitter,
    OnDestroy,
    AfterViewInit,
} from '@angular/core';
import {Breakdown} from '../../../../../../../app.constants';
import {BidModifierImportFormStore} from './services/bid-modifier-import-form.store';
import {APP_CONFIG} from '../../../../../../../app.config';
import {Subject, Observable, merge} from 'rxjs';
import {distinctUntilChanged, takeUntil, map, tap} from 'rxjs/operators';
import {BidModifierImportFormApi} from './types/bid-modifier-import-form-api';

@Component({
    selector: 'zem-bid-modifier-import-form',
    templateUrl: './bid-modifier-import-form.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [BidModifierImportFormStore],
})
export class BidModifierImportFormComponent
    implements OnInit, AfterViewInit, OnDestroy {
    @Input()
    adGroupId: number;
    @Input()
    breakdown: Breakdown;
    @Output()
    componentReady = new EventEmitter<BidModifierImportFormApi>();
    @Output()
    fileChange = new EventEmitter<File>();

    Breakdown = Breakdown;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(public store: BidModifierImportFormStore) {}

    ngOnInit(): void {
        this.store.init(this.adGroupId, this.breakdown);
        this.subscribeToStateUpdates();
    }

    ngAfterViewInit(): void {
        this.componentReady.emit({
            executeImport: this.executeImport.bind(this),
        });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
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

    executeImport(): Promise<boolean> {
        return this.store.import();
    }

    onFilesChange($event: File[]): void {
        const file: File = $event.length > 0 ? $event[0] : null;
        this.store.updateFile(file);
    }

    private subscribeToStateUpdates() {
        merge(this.fileUpdater$())
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe();
    }

    private fileUpdater$(): Observable<File> {
        return this.store.state$.pipe(
            map(state => state.file),
            distinctUntilChanged(),
            tap(file => this.fileChange.emit(file))
        );
    }
}
