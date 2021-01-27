import {WorkerAction} from './worker.action';
import {ActionMessage} from '../shared/types/action-message';
import {buildHierarchy} from '../shared/helpers/hierarchy.helpers';
import {Hierarchy} from '../shared/types/hierarchy';

export class BuildHierarchyAction implements WorkerAction {
    async run(message: ActionMessage): Promise<any> {
        return new Promise<any>(resolve => {
            const hierarchy: Hierarchy = buildHierarchy(message.payload);
            resolve(hierarchy);
        });
    }
}
