import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {RuleEditFormComponent} from './components/rule-edit-form/rule-edit-form.component';
import {RuleEditFormActionComponent} from './components/rule-edit-form-action/rule-edit-form-action.component';
import {RuleEditFormNotificationComponent} from './components/rule-edit-form-notification/rule-edit-form-notification.component';
import {RuleEditFormConditionsComponent} from './components/rule-edit-form-conditions/rule-edit-form-conditions.component';
import {RuleEditFormConditionComponent} from './components/rule-edit-form-condition/rule-edit-form-condition.component';
import {RuleEditFormConditionModifierComponent} from './components/rule-edit-form-condition-modifier/rule-edit-form-condition-modifier.component';
import {RulesHistoriesGridComponent} from './components/rules-histories-grid/rules-histories-grid.component';
import {RulesHistoriesView} from './views/rules-histories/rules-histories.view';

@NgModule({
    declarations: [
        RuleEditFormComponent,
        RuleEditFormActionComponent,
        RuleEditFormNotificationComponent,
        RuleEditFormConditionsComponent,
        RuleEditFormConditionComponent,
        RuleEditFormConditionModifierComponent,
        RulesHistoriesGridComponent,
        RulesHistoriesView,
    ],
    imports: [SharedModule],
    exports: [RuleEditFormComponent],
    entryComponents: [RulesHistoriesView],
})
export class RulesModule {}
