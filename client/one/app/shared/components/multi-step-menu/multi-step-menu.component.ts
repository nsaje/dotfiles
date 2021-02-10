import './multi-step-menu.component.less';

import {
    ChangeDetectionStrategy,
    Component,
    Input,
    OnChanges,
} from '@angular/core';
import {MultiStepMenuOption} from './types/multi-step-menu-option';
import {MultiStepMenuStep} from './types/multi-step-menu-step';
import {MultiStepMenuItem} from './types/multi-step-menu-item';
import {isDefined} from '../../helpers/common.helpers';

@Component({
    selector: 'zem-multi-step-menu',
    templateUrl: './multi-step-menu.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MultiStepMenuComponent implements OnChanges {
    @Input()
    options: MultiStepMenuOption[];

    steps: MultiStepMenuStep[];
    currentStep: number = 1;

    private nextStepId: number;

    ngOnChanges() {
        this.nextStepId = 1;
        this.steps = this.convertOptionsToSteps(this.options);
    }

    private convertOptionsToSteps(
        options: MultiStepMenuOption[],
        parentStepId: number = null,
        name: string = null
    ): MultiStepMenuStep[] {
        const currentStep: MultiStepMenuStep = {
            stepId: this.nextStepId,
            name,
            parentStepId,
            items: [],
        };
        this.nextStepId++;
        const nextSteps: MultiStepMenuStep[] = [];

        options.forEach(option => {
            const newItem: MultiStepMenuItem = {
                name: option.name,
                description: option.description,
                hasNextStep: isDefined(option.nextOptions),
                handler: null,
            };

            if (option.nextOptions) {
                const childSteps: MultiStepMenuStep[] = this.convertOptionsToSteps(
                    option.nextOptions,
                    currentStep.stepId,
                    option.name
                );
                nextSteps.push(...childSteps);
                newItem.handler = () => this.goToStep(childSteps[0].stepId);
            } else {
                newItem.handler = option.handler;
            }
            currentStep.items.push(newItem);
        });

        return [currentStep, ...nextSteps];
    }

    private goToStep(stepId: number) {
        this.currentStep = stepId;
    }
}
