import './file-selector.component.less';

import {
    Component,
    Input,
    OnInit,
    Output,
    EventEmitter,
    OnDestroy,
    ChangeDetectionStrategy,
    ViewChild,
    ElementRef,
    AfterViewInit,
} from '@angular/core';
import {
    NgxFileDropComponent,
    NgxFileDropEntry,
    FileSystemFileEntry,
} from 'ngx-file-drop';
import {Subject} from 'rxjs';
import {takeUntil} from 'rxjs/operators';
import {FileSelectorApi} from './types/file-selector-api';

@Component({
    selector: 'zem-file-selector',
    templateUrl: './file-selector.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FileSelectorComponent extends NgxFileDropComponent
    implements OnInit, OnDestroy, AfterViewInit {
    @Input()
    isMultiple: boolean = true;
    @Input()
    showBrowseButton: boolean = false;
    @Input()
    browseButtonLabel: string;
    @Output()
    filesChange = new EventEmitter<File[]>();
    @Output()
    componentReady = new EventEmitter<FileSelectorApi>();

    @ViewChild('fileSelector', {static: false})
    fileSelector: ElementRef;

    private ngUnsubscribe$: Subject<undefined> = new Subject();

    filesToUpload: NgxFileDropEntry[];

    ngOnInit(): void {
        this.filesToUpload = [];
        this.onFileDrop
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(($event: NgxFileDropEntry[]) => {
                this.filesToUpload = this.isMultiple ? $event : [$event[0]];
                this.convertFromFilesToUploadToFiles(this.filesToUpload).then(
                    (files: File[]) => {
                        this.filesChange.emit(files);
                    }
                );
            });
    }

    ngAfterViewInit(): void {
        this.componentReady.emit({
            clearFilesToUpload: this.clearFilesToUpload.bind(this),
        });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
        super.ngOnDestroy();
    }

    clearFilesToUpload(): void {
        this.filesToUpload = [];
    }

    removeFile(fileToUpload: NgxFileDropEntry): void {
        this.filesToUpload.splice(this.filesToUpload.indexOf(fileToUpload), 1);
        this.convertFromFilesToUploadToFiles(this.filesToUpload).then(
            (files: File[]) => {
                this.filesChange.emit(files);
            }
        );
    }

    private async convertFromFilesToUploadToFiles(
        filesToUpload: NgxFileDropEntry[]
    ): Promise<File[]> {
        const files: File[] = [];
        // The NgxFileDropEntry has a fileEntry property, which is of type FileSystemEntry.
        // The FileSystemEntry interface's method file() is used to read the file from
        // the directory entry (async operation). After the file has been read a callback
        // function is called. We use promises to resolve the file() response.
        await Promise.all(
            filesToUpload.map(async (fileToUpload: NgxFileDropEntry) => {
                if (fileToUpload.fileEntry.isFile) {
                    const file = await this.getFilePromise(fileToUpload);
                    files.push(file);
                }
            })
        );
        return files;
    }

    private getFilePromise(fileToUpload: NgxFileDropEntry): Promise<File> {
        return new Promise<File>(resolve => {
            const fileEntry = fileToUpload.fileEntry as FileSystemFileEntry;
            fileEntry.file((file: File) => {
                return resolve(file);
            });
        });
    }
}
