import {Hack} from '../common/hack';
import {Currency} from '../../../../app.constants';
import {Deal} from '../common/deal';
import {CampaignGoalsDefaults} from './campaign-goals-defaults';
import {CampaignBudgetsOverview} from './campaign-budgets-overview';
import {CampaignBudget} from './campaign-budget';
import {AccountCredit} from '../account/account-credit';

export interface CampaignExtras {
    currency: Currency;
    goalsDefaults: CampaignGoalsDefaults;
    budgetsOverview: CampaignBudgetsOverview;
    budgetsDepleted: CampaignBudget[];
    accountCredits: AccountCredit[];
}
