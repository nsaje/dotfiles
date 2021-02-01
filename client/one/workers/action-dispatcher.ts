import {BuildHierarchyAction} from './actions/build-hierarchy.action';
import {WorkerAction} from './actions/worker.action';
import {ActionMessage} from './shared/types/action-message';
import {ActionTopic} from './shared/workers.constants';
import {ActionProvider} from './types/action-provider';

export class ActionDispatcher {
    private readonly worker: Worker;

    readonly providers: ActionProvider[] = [
        {
            provide: ActionTopic.BUILD_HIERARCHY,
            useClass: BuildHierarchyAction,
        },
    ];

    constructor(_worker: any) {
        this.worker = _worker;
    }

    async dispatch($event: MessageEvent): Promise<void> {
        const actionMessage = $event.data as ActionMessage;
        const action = this.getAction(actionMessage);
        if (action) {
            const result: any = await action.run(actionMessage);
            this.worker.postMessage(result);
        } else {
            throw Error('Worker action not provided');
        }
    }

    private getAction(message: ActionMessage): WorkerAction {
        if (message && 'topic' in message) {
            const provider = this.providers.find(
                p => p.provide === message.topic
            );
            if (provider) {
                return new provider.useClass();
            }
        }
        return null;
    }
}
