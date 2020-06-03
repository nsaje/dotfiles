import './note-cell.component.less';
import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {NoteRendererParams} from './types/note.renderer-params';

@Component({
    templateUrl: './note-cell.component.html',
})
export class NoteCellComponent<T> implements ICellRendererAngularComp {
    params: NoteRendererParams<T>;
    mainContent: string;
    note: string;

    agInit(params: NoteRendererParams<T>) {
        this.params = params;
        this.mainContent = params.getMainContent(params.data);
        this.note = params.getNote(params.data);
    }

    refresh(): boolean {
        return false;
    }
}
