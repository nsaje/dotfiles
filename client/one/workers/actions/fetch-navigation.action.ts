import {WorkerAction} from './worker.action';
import {ActionMessage} from '../shared/types/action-message';

export class FetchNavigationAction implements WorkerAction {
    async run(message: ActionMessage): Promise<any> {
        return new Promise<any>(resolve => {
            const http = new XMLHttpRequest();
            http.open('GET', message.payload.url, false);
            http.send();
            resolve(JSON.parse(http.responseText));
        });
    }
}
