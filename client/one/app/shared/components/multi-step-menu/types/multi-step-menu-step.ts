import {MultiStepMenuItem} from './multi-step-menu-item';

export interface MultiStepMenuStep {
    stepId: number;
    name: string;
    parentStepId: number;
    items: MultiStepMenuItem[];
}
