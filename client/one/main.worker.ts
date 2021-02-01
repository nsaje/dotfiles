import {ActionDispatcher} from './workers/action-dispatcher';

const worker: Worker = self as any;

worker.addEventListener('message', ($event: MessageEvent) => {
    const dispatcher = new ActionDispatcher(worker);
    dispatcher.dispatch($event);
});
