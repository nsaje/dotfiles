import {Hack} from '../common/hack';
import {Currency} from '../../../../app.constants';
import {Deal} from '../common/deal';
import {CampaignGoalsDefaults} from '../../../../features/entity-manager/types/campaign-goals-defaults';
import {CampaignBudgetsOverview} from '../../../../features/entity-manager/types/campaign-budgets-overview';

export interface CampaignExtras {
    currency: Currency;
    goalsDefaults: CampaignGoalsDefaults;
    budgetsOverview: CampaignBudgetsOverview;
}
