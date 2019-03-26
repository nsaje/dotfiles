import './file-selector.component.less';

import {
    Component,
    Input,
    OnInit,
    Output,
    EventEmitter,
    OnDestroy,
    ChangeDetectionStrategy,
} from '@angular/core';
import {
    FileComponent,
    UploadEvent,
    UploadFile,
    FileSystemFileEntry,
} from 'ngx-file-drop';
import {Subject} from 'rxjs';
import {takeUntil} from 'rxjs/operators';

@Component({
    selector: 'zem-file-selector',
    templateUrl: './file-selector.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FileSelectorComponent extends FileComponent
    implements OnInit, OnDestroy {
    @Input()
    isMultiple: boolean = true;
    @Input()
    showBrowseButton: boolean = false;
    @Input()
    browseButtonLabel: string;
    @Output()
    filesChange = new EventEmitter<File[]>();

    private ngUnsubscribe$: Subject<undefined> = new Subject();

    filesToUpload: UploadFile[];

    ngOnInit(): void {
        this.filesToUpload = [];
        this.onFileDrop
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(($event: UploadEvent) => {
                this.filesToUpload = this.isMultiple
                    ? $event.files
                    : [$event.files[0]];
                this.convertFromUploadFilesToFiles(this.filesToUpload).then(
                    (files: File[]) => {
                        this.filesChange.emit(files);
                    }
                );
            });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
        super.ngOnDestroy();
    }

    removeFile(fileToUpload: UploadFile): void {
        this.filesToUpload.splice(this.filesToUpload.indexOf(fileToUpload), 1);
        this.convertFromUploadFilesToFiles(this.filesToUpload).then(
            (files: File[]) => {
                this.filesChange.emit(files);
            }
        );
    }

    private async convertFromUploadFilesToFiles(
        filesToUpload: UploadFile[]
    ): Promise<File[]> {
        const files: File[] = [];
        // The UploadFile has a fileEntry property, which is of type FileSystemEntry.
        // The FileSystemEntry interface's method file() is used to read the file from
        // the directory entry (async operation). After the file has been read a callback
        // function is called. We use promises to resolve the file() response.
        await Promise.all(
            filesToUpload.map(async (fileToUpload: UploadFile) => {
                if (fileToUpload.fileEntry.isFile) {
                    const file = await this.getFilePromise(fileToUpload);
                    files.push(file);
                }
            })
        );
        return files;
    }

    private getFilePromise(fileToUpload: UploadFile): Promise<File> {
        return new Promise<File>(resolve => {
            const fileEntry = fileToUpload.fileEntry as FileSystemFileEntry;
            fileEntry.file((file: File) => {
                return resolve(file);
            });
        });
    }
}
