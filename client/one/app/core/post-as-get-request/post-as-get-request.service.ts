import {Injectable, Inject} from '@angular/core';
import {DOCUMENT} from '@angular/common';
import {RequestPayload} from '../../shared/types/request-payload';

@Injectable()
export class PostAsGetRequestService {
    constructor(@Inject(DOCUMENT) private document: Document) {}

    postAsGet(payload: RequestPayload, url: string) {
        const form = this.document.createElement('FORM') as HTMLFormElement;
        form.action = url;
        form.method = 'POST';
        form.target = '_blank';

        const input = this.document.createElement('INPUT') as HTMLInputElement;
        input.name = 'data';
        input.type = 'hidden';
        input.value = JSON.stringify(payload);

        form.appendChild(input);
        this.document.body.appendChild(form);
        form.submit();
        this.document.body.removeChild(form);
    }
}
