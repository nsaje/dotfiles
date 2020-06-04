import {Hack} from '../common/hack';
import {Currency, Language} from '../../../../app.constants';
import {Deal} from '../common/deal';
import {CampaignGoalsDefaults} from './campaign-goals-defaults';
import {CampaignBudgetsOverview} from './campaign-budgets-overview';
import {CampaignBudget} from './campaign-budget';
import {Credit} from '../common/credit';
import {User} from '../common/user';

export interface CampaignExtras {
    agencyId: string;
    archived: boolean;
    language: Language;
    canRestore: boolean;
    campaignManagers: User[];
    currency: Currency;
    goalsDefaults: CampaignGoalsDefaults;
    budgetsOverview: CampaignBudgetsOverview;
    budgetsDepleted: CampaignBudget[];
    credits: Credit[];
    hacks: Hack[];
    deals: Deal[];
}
