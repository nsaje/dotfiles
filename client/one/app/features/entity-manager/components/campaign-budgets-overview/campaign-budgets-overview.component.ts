import './campaign-budgets-overview.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    SimpleChanges,
    OnChanges,
} from '@angular/core';
import {CampaignBudgetsOverview} from '../../../../core/entities/types/campaign/campaign-budgets-overview';
import {Currency} from '../../../../app.constants';
import * as currencyHelpers from '../../../../shared/helpers/currency.helpers';

@Component({
    selector: 'zem-campaign-budgets-overview',
    templateUrl: './campaign-budgets-overview.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CampaignBudgetsOverviewComponent implements OnChanges {
    @Input()
    overview: CampaignBudgetsOverview;
    @Input()
    currency: Currency;
    @Input()
    showLicenseFee: boolean;
    @Input()
    showServiceFee: boolean;
    @Input()
    showMargin: boolean;

    formattedOverview: CampaignBudgetsOverview;

    ngOnChanges(changes: SimpleChanges) {
        if (changes.overview || changes.currency) {
            this.formattedOverview = {
                campaignSpend: currencyHelpers.getValueInCurrency(
                    this.overview.campaignSpend,
                    this.currency
                ),
                mediaSpend: currencyHelpers.getValueInCurrency(
                    this.overview.mediaSpend,
                    this.currency
                ),
                baseMediaSpend: currencyHelpers.getValueInCurrency(
                    this.overview.baseMediaSpend,
                    this.currency
                ),
                dataSpend: currencyHelpers.getValueInCurrency(
                    this.overview.dataSpend,
                    this.currency
                ),
                baseDataSpend: currencyHelpers.getValueInCurrency(
                    this.overview.baseDataSpend,
                    this.currency
                ),
                licenseFee: currencyHelpers.getValueInCurrency(
                    this.overview.licenseFee,
                    this.currency
                ),
                serviceFee: currencyHelpers.getValueInCurrency(
                    this.overview.serviceFee,
                    this.currency
                ),
                margin: currencyHelpers.getValueInCurrency(
                    this.overview.margin,
                    this.currency
                ),
                availableBudgetsSum: currencyHelpers.getValueInCurrency(
                    this.overview.availableBudgetsSum,
                    this.currency
                ),
                unallocatedCredit: currencyHelpers.getValueInCurrency(
                    this.overview.unallocatedCredit,
                    this.currency
                ),
            };
        }
    }
}
