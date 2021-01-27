import {Type} from '@angular/core';
import {ActionTopic} from '../shared/workers.constants';
import {WorkerAction} from '../actions/worker.action';

export interface ActionProvider {
    provide: ActionTopic;
    useClass: Type<WorkerAction>;
}
