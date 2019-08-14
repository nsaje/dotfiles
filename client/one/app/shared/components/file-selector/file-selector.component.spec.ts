import {
    TestBed,
    ComponentFixture,
    fakeAsync,
    tick,
} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {FileSelectorComponent} from './file-selector.component';
import {NgxFileDropEntry, FileSystemFileEntry} from 'ngx-file-drop';

describe('FileSelectorComponent', () => {
    let component: FileSelectorComponent;
    let fixture: ComponentFixture<FileSelectorComponent>;
    let mockedFile: any;
    let mockedFileEntry: FileSystemFileEntry;
    let mockedUploadFile: NgxFileDropEntry;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [FileSelectorComponent],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(FileSelectorComponent);
        component = fixture.componentInstance;

        mockedFile = {
            name: 'file.csv',
        };
        mockedFileEntry = {
            name: mockedFile.name,
            isDirectory: false,
            isFile: true,
            file: (callback: (file: any) => void): void => {
                callback(mockedFile);
            },
        };
        mockedUploadFile = new NgxFileDropEntry(
            mockedFileEntry.name,
            mockedFileEntry
        );
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should correctly emit files on fileDrop call', fakeAsync(() => {
        component.ngOnInit();

        spyOn(component.filesChange, 'emit').and.stub();

        component.onFileDrop.emit([mockedUploadFile]);
        tick();

        expect(component.filesChange.emit).toHaveBeenCalledTimes(1);
        expect(component.filesChange.emit).toHaveBeenCalledWith([mockedFile]);
    }));

    it('should correctly emit files on removeFile call', fakeAsync(() => {
        component.ngOnInit();
        component.filesToUpload = [mockedUploadFile];

        spyOn(component.filesChange, 'emit').and.stub();
        component.removeFile(mockedUploadFile);
        tick();

        expect(component.filesChange.emit).toHaveBeenCalledTimes(1);
        expect(component.filesChange.emit).toHaveBeenCalledWith([]);
    }));
});
