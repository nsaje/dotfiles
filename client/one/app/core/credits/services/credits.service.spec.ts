import {CreditsEndpoint} from './credits.endpoint';
import {CreditsService} from './credits.service';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {Credit} from '../types/credit';
import {asapScheduler, of} from 'rxjs';
import {CreditTotal} from '../types/credit-total';
import {Currency, CreditStatus} from '../../../app.constants';
import {CreditRefund} from '../types/credit-refund';
import {CampaignBudget} from '../../entities/types/campaign/campaign-budget';
import * as clone from 'clone';

describe('CreditsService', () => {
    let service: CreditsService;
    let creditsEndpointStub: jasmine.SpyObj<CreditsEndpoint>;
    let requestStateUpdater: RequestStateUpdater;

    const creditId = '123';
    const agencyId = '1234';
    const accountId = '5678';
    const limit = 20;
    const offset = 0;
    const date = new Date(1970, 1, 1);

    const mockedTotals: CreditTotal[] = [
        {
            total: '100.00',
            allocated: '100.00',
            past: '0.00',
            available: '0.00',
            currency: Currency.USD,
        },
    ];

    const mockedCredits: Credit[] = [
        {
            id: '123',
            accountId: accountId,
            agencyId: agencyId,
            total: '300.00',
            startDate: date,
            endDate: new Date(1970, 2, 1),
            licenseFee: '15',
            currency: Currency.USD,
            contractId: '4321',
            contractNumber: '1234',
            status: CreditStatus.SIGNED,
            comment: null,
            amount: 50,
        },
        {
            id: '321',
            accountId: accountId,
            agencyId: agencyId,
            total: '300.00',
            startDate: date,
            endDate: new Date(1970, 2, 1),
            licenseFee: '15',
            currency: Currency.USD,
            contractId: '4321',
            contractNumber: '1234',
            status: CreditStatus.SIGNED,
            comment: null,
            amount: 50,
        },
    ];

    const mockedCreditRefunds: CreditRefund[] = [
        {
            id: '789',
            creditId: '123',
            accountId: accountId,
            amount: 100,
            startDate: date,
            effectiveMargin: '0',
            comment: null,
        },
        {
            id: '987',
            creditId: '321',
            accountId: accountId,
            amount: 100,
            startDate: date,
            effectiveMargin: '0',
            comment: null,
        },
    ];

    const mockedBudgets: CampaignBudget[] = [
        {
            id: '456',
            creditId: '123',
            canEditAmount: false,
            canEditEndDate: false,
            canEditStartDate: false,
            comment: null,
            startDate: date,
            endDate: date,
            amount: '20',
            margin: '5',
        },
    ];

    beforeEach(() => {
        creditsEndpointStub = jasmine.createSpyObj(CreditsEndpoint.name, [
            'list',
            'create',
            'edit',
            'totals',
            'listBudgets',
            'listRefunds',
            'createRefund',
        ]);

        service = new CreditsService(creditsEndpointStub);

        requestStateUpdater = (requestName, requestState) => {};
    });

    it('should list active credits via endpoint', () => {
        creditsEndpointStub.list.and
            .returnValue(of(mockedCredits, asapScheduler))
            .calls.reset();

        service
            .listActive(agencyId, accountId, offset, limit, requestStateUpdater)
            .subscribe(credits => {
                expect(credits).toEqual(mockedCredits);
            });

        expect(creditsEndpointStub.list).toHaveBeenCalledTimes(1);
        expect(creditsEndpointStub.list).toHaveBeenCalledWith(
            agencyId,
            accountId,
            true,
            offset,
            limit,
            requestStateUpdater
        );
    });

    it('should list past credits via endpoint', () => {
        creditsEndpointStub.list.and
            .returnValue(of(mockedCredits, asapScheduler))
            .calls.reset();

        service
            .listPast(agencyId, accountId, offset, limit, requestStateUpdater)
            .subscribe(credits => {
                expect(credits).toEqual(mockedCredits);
            });

        expect(creditsEndpointStub.list).toHaveBeenCalledTimes(1);
        expect(creditsEndpointStub.list).toHaveBeenCalledWith(
            agencyId,
            accountId,
            false,
            offset,
            limit,
            requestStateUpdater
        );
    });

    it('should create credit via endpoint', () => {
        const mockedCredit = clone(mockedCredits[0]);
        mockedCredit.id = undefined;

        creditsEndpointStub.create.and
            .returnValue(of(mockedCredit, asapScheduler))
            .calls.reset();

        service.save(mockedCredit, requestStateUpdater).subscribe(credits => {
            expect(credits).toEqual(mockedCredit);
        });

        expect(creditsEndpointStub.create).toHaveBeenCalledTimes(1);
        expect(creditsEndpointStub.create).toHaveBeenCalledWith(
            mockedCredit,
            requestStateUpdater
        );
    });

    it('should edit credit via endpoint', () => {
        const mockedCredit = clone(mockedCredits[0]);

        creditsEndpointStub.edit.and
            .returnValue(of(mockedCredit, asapScheduler))
            .calls.reset();

        service.save(mockedCredit, requestStateUpdater).subscribe(credits => {
            expect(credits).toEqual(mockedCredit);
        });

        expect(creditsEndpointStub.edit).toHaveBeenCalledTimes(1);
        expect(creditsEndpointStub.edit).toHaveBeenCalledWith(
            mockedCredit,
            requestStateUpdater
        );
    });

    it('should list totals via endpoint', () => {
        creditsEndpointStub.totals.and
            .returnValue(of(mockedTotals, asapScheduler))
            .calls.reset();

        service
            .totals(agencyId, accountId, requestStateUpdater)
            .subscribe(totals => {
                expect(totals).toEqual(mockedTotals);
            });

        expect(creditsEndpointStub.totals).toHaveBeenCalledTimes(1);
        expect(creditsEndpointStub.totals).toHaveBeenCalledWith(
            agencyId,
            accountId,
            requestStateUpdater
        );
    });

    it('should list budgets via endpoint', () => {
        creditsEndpointStub.listBudgets.and
            .returnValue(of(mockedBudgets, asapScheduler))
            .calls.reset();

        service
            .listBudgets(creditId, requestStateUpdater)
            .subscribe(budgets => {
                expect(budgets).toEqual(mockedBudgets);
            });

        expect(creditsEndpointStub.listBudgets).toHaveBeenCalledTimes(1);
        expect(creditsEndpointStub.listBudgets).toHaveBeenCalledWith(
            creditId,
            requestStateUpdater
        );
    });

    it('should list refunds via endpoint', () => {
        creditsEndpointStub.listRefunds.and
            .returnValue(of(mockedCreditRefunds, asapScheduler))
            .calls.reset();

        service
            .listRefunds(creditId, offset, limit, requestStateUpdater)
            .subscribe(creditRefunds => {
                expect(creditRefunds).toEqual(mockedCreditRefunds);
            });

        expect(creditsEndpointStub.listRefunds).toHaveBeenCalledTimes(1);
        expect(creditsEndpointStub.listRefunds).toHaveBeenCalledWith(
            creditId,
            offset,
            limit,
            requestStateUpdater
        );
    });

    it('should create refund via endpoint', () => {
        const mockedCreditRefund = clone(mockedCreditRefunds[0]);
        mockedCreditRefund.id = undefined;

        creditsEndpointStub.createRefund.and
            .returnValue(of(mockedCreditRefund, asapScheduler))
            .calls.reset();

        service
            .createRefund(creditId, mockedCreditRefund, requestStateUpdater)
            .subscribe(creditRefund => {
                expect(creditRefund).toEqual(mockedCreditRefund);
            });

        expect(creditsEndpointStub.createRefund).toHaveBeenCalledTimes(1);
        expect(creditsEndpointStub.createRefund).toHaveBeenCalledWith(
            creditId,
            mockedCreditRefund,
            requestStateUpdater
        );
    });
});
