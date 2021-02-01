import {ActionTopic} from '../workers.constants';

export interface ActionMessage {
    topic: ActionTopic;
    payload: any;
}
