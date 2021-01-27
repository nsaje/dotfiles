import {ActionMessage} from '../shared/types/action-message';

export interface WorkerAction {
    run(message: ActionMessage): Promise<any>;
}
