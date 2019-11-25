import {NgModule} from '@angular/core';
import {RulesEndpoint} from './services/rules.endpoint';
import {RulesService} from './services/rules.service';

@NgModule({
    providers: [RulesEndpoint, RulesService],
})
export class RulesModule {}
