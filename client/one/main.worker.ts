import {ActionDispatcher} from './workers/action-dispatcher';
import {ActionMessage} from './workers/shared/types/action-message';

const worker: Worker = self as any;
const dispatcher = new ActionDispatcher(worker);
const payload: any[] = [];

worker.addEventListener('message', ($event: MessageEvent) => {
    const message = JSON.parse($event.data) as ActionMessage;
    if (message.payloadLength) {
        // Communicating Large Objects with Web Workers in javascript
        // https://developers.redhat.com/blog/2014/05/20/communicating-large-objects-with-web-workers-in-javascript/
        payload.push(message.payload);
        if (payload.length === message.payloadLength) {
            dispatcher.dispatch({
                topic: message.topic,
                payload: payload,
            });
        }
    } else {
        dispatcher.dispatch(message);
    }
});
