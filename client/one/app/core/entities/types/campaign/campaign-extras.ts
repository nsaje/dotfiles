import {Hack} from '../common/hack';
import {Currency, Language} from '../../../../app.constants';
import {Deal} from '../common/deal';
import {CampaignGoalsDefaults} from './campaign-goals-defaults';
import {CampaignBudgetsOverview} from './campaign-budgets-overview';
import {CampaignBudget} from './campaign-budget';
import {AccountCredit} from '../account/account-credit';
import {User} from '../common/user';

export interface CampaignExtras {
    archived: boolean;
    language: Language;
    canArchive: boolean;
    canRestore: boolean;
    campaignManagers: User[];
    currency: Currency;
    goalsDefaults: CampaignGoalsDefaults;
    budgetsOverview: CampaignBudgetsOverview;
    budgetsDepleted: CampaignBudget[];
    accountCredits: AccountCredit[];
    hacks: Hack[];
    deals: Deal[];
}
