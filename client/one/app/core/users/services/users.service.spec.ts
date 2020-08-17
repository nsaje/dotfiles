import {asapScheduler, of} from 'rxjs';
import * as clone from 'clone';
import {tick, fakeAsync} from '@angular/core/testing';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {UsersEndpoint} from './users.endpoint';
import {UsersService} from './users.service';
import {User} from '../types/user';
import {UserStatus} from '../../../app.constants';

describe('UsersService', () => {
    let service: UsersService;
    let usersEndpointStub: jasmine.SpyObj<UsersEndpoint>;
    let requestStateUpdater: RequestStateUpdater;

    let mockedCurrentUser: User;
    let mockedUser: User;
    let mockedUsers: User[];
    let mockedCreateUsers: User[];
    let mockedUserId: string;
    let mockedAgencyId: string;
    let mockedAccountId: string;

    beforeEach(() => {
        usersEndpointStub = jasmine.createSpyObj(UsersEndpoint.name, [
            'current',
            'list',
            'create',
            'validate',
            'get',
            'edit',
            'remove',
            'resendEmail',
        ]);
        service = new UsersService(usersEndpointStub);
        requestStateUpdater = (requestName, requestState) => {};

        mockedAgencyId = '71';
        mockedAccountId = '55';
        mockedUserId = '456346';
        mockedUsers = [
            {
                id: '10000000',
                email: 'test.user@outbrain.com',
                firstName: 'Test',
                lastName: 'User',
                entityPermissions: [
                    {
                        agencyId: mockedAgencyId,
                        permission: 'read',
                    },
                ],
                status: UserStatus.ACTIVE,
            },
            {
                id: '10000001',
                email: 'pat@ajeto.cz',
                firstName: 'Pat',
                entityPermissions: [
                    {
                        agencyId: mockedAccountId,
                        permission: 'read',
                    },
                    {
                        agencyId: mockedAccountId,
                        permission: 'user',
                    },
                ],
                status: UserStatus.ACTIVE,
            },
            {
                id: '10000002',
                email: 'mat@ajeto.cz',
                firstName: 'Mat',
                entityPermissions: [
                    {
                        agencyId: mockedAccountId,
                        permission: 'read',
                    },
                    {
                        agencyId: mockedAccountId,
                        permission: 'budget',
                    },
                ],
                status: UserStatus.ACTIVE,
            },
        ];
        mockedUser = clone(mockedUsers[0]);

        mockedCreateUsers = [
            {
                email: 'test.user@outbrain.com',
                entityPermissions: [
                    {
                        agencyId: mockedAccountId,
                        permission: 'read',
                    },
                    {
                        agencyId: mockedAccountId,
                        permission: 'user',
                    },
                ],
                status: UserStatus.ACTIVE,
            },
            {
                email: 'pat@ajeto.cz',
                entityPermissions: [
                    {
                        agencyId: mockedAccountId,
                        permission: 'read',
                    },
                    {
                        agencyId: mockedAccountId,
                        permission: 'user',
                    },
                ],
                status: UserStatus.ACTIVE,
            },
            {
                email: 'mat@ajeto.cz',
                entityPermissions: [
                    {
                        agencyId: mockedAccountId,
                        permission: 'read',
                    },
                    {
                        agencyId: mockedAccountId,
                        permission: 'user',
                    },
                ],
                status: UserStatus.ACTIVE,
            },
        ];

        mockedCurrentUser = {
            id: mockedUserId,
            email: 'test@test.com',
            firstName: 'test',
            lastName: 'test',
            name: 'test tests',
            status: UserStatus.ACTIVE,
            agencies: [71],
            timezoneOffset: -4000,
            intercomUserHash: '$test$',
            defaultCsvSeparator: ',',
            defaultCsvDecimalSeparator: '.',
            permissions: [
                {
                    permission: 'permission.public_1',
                    isPublic: true,
                },
                {
                    permission: 'permission.public_2',
                    isPublic: true,
                },
                {
                    permission: 'permission.internal_1',
                    isPublic: false,
                },
                {
                    permission: 'permission.internal_2',
                    isPublic: false,
                },
            ],
            entityPermissions: [
                {
                    agencyId: '123',
                    permission: 'read',
                },
                {
                    agencyId: '123',
                    permission: 'write',
                },
            ],
        };
    });

    it('should get current user via endpoint', () => {
        usersEndpointStub.current.and
            .returnValue(of(mockedCurrentUser, asapScheduler))
            .calls.reset();

        service.current(requestStateUpdater).subscribe(user => {
            expect(user).toEqual(mockedCurrentUser);
        });

        expect(usersEndpointStub.current).toHaveBeenCalledTimes(1);
        expect(usersEndpointStub.current).toHaveBeenCalledWith(
            requestStateUpdater
        );
    });

    it('should get users via endpoint', () => {
        const limit = 10;
        const offset = 0;
        const keyword = 'ajeto';
        const showInternal = true;
        usersEndpointStub.list.and
            .returnValue(of(mockedUsers, asapScheduler))
            .calls.reset();

        service
            .list(
                mockedAgencyId,
                mockedAccountId,
                offset,
                limit,
                keyword,
                showInternal,
                requestStateUpdater
            )
            .subscribe(users => {
                expect(users).toEqual(mockedUsers);
            });
        expect(usersEndpointStub.list).toHaveBeenCalledTimes(1);
        expect(usersEndpointStub.list).toHaveBeenCalledWith(
            mockedAgencyId,
            mockedAccountId,
            offset,
            limit,
            keyword,
            showInternal,
            requestStateUpdater
        );
    });

    it('should create new users', fakeAsync(() => {
        usersEndpointStub.create.and
            .returnValue(of(mockedUsers, asapScheduler))
            .calls.reset();

        service
            .create(
                mockedCreateUsers,
                mockedAgencyId,
                mockedAccountId,
                requestStateUpdater
            )
            .subscribe(user => {
                expect(user).toEqual(mockedUsers);
            });
        tick();

        expect(usersEndpointStub.create).toHaveBeenCalledTimes(1);
        expect(usersEndpointStub.create).toHaveBeenCalledWith(
            mockedCreateUsers,
            mockedAgencyId,
            mockedAccountId,
            requestStateUpdater
        );
    }));

    it('should get user via endpoint', () => {
        usersEndpointStub.get.and
            .returnValue(of(mockedUser, asapScheduler))
            .calls.reset();

        service
            .get(
                mockedUserId,
                mockedAgencyId,
                mockedAccountId,
                requestStateUpdater
            )
            .subscribe(user => {
                expect(user).toEqual(mockedUser);
            });
        expect(usersEndpointStub.get).toHaveBeenCalledTimes(1);
        expect(usersEndpointStub.get).toHaveBeenCalledWith(
            mockedUserId,
            mockedAgencyId,
            mockedAccountId,
            requestStateUpdater
        );
    });

    it('should edit user via endpoint', () => {
        const mockedNewUser = clone(mockedUsers[0]);
        usersEndpointStub.edit.and
            .returnValue(of(mockedUser, asapScheduler))
            .calls.reset();

        service
            .edit(
                mockedNewUser,
                mockedAgencyId,
                mockedAccountId,
                requestStateUpdater
            )
            .subscribe(newUser => {
                expect(newUser).toEqual(mockedNewUser);
            });

        expect(usersEndpointStub.edit).toHaveBeenCalledTimes(1);
        expect(usersEndpointStub.edit).toHaveBeenCalledWith(
            mockedNewUser,
            mockedAgencyId,
            mockedAccountId,
            requestStateUpdater
        );
    });

    it('should remove user via endpoint', () => {
        usersEndpointStub.remove.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();

        service
            .remove(
                mockedUserId,
                mockedAgencyId,
                mockedAccountId,
                requestStateUpdater
            )
            .subscribe(x => {});
        expect(usersEndpointStub.remove).toHaveBeenCalledTimes(1);
        expect(usersEndpointStub.remove).toHaveBeenCalledWith(
            mockedUserId,
            mockedAgencyId,
            mockedAccountId,
            requestStateUpdater
        );
    });

    it('should validate user via endpoint', () => {
        usersEndpointStub.validate.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();

        service
            .validate(
                mockedUser,
                mockedAgencyId,
                mockedAccountId,
                requestStateUpdater
            )
            .subscribe(x => {});
        expect(usersEndpointStub.validate).toHaveBeenCalledTimes(1);
        expect(usersEndpointStub.validate).toHaveBeenCalledWith(
            mockedUser,
            mockedAgencyId,
            mockedAccountId,
            requestStateUpdater
        );
    });

    it('should resend email user via endpoint', () => {
        usersEndpointStub.resendEmail.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();

        service
            .resendEmail(
                mockedUserId,
                mockedAgencyId,
                mockedAccountId,
                requestStateUpdater
            )
            .subscribe(x => {});
        expect(usersEndpointStub.resendEmail).toHaveBeenCalledTimes(1);
        expect(usersEndpointStub.resendEmail).toHaveBeenCalledWith(
            mockedUserId,
            mockedAgencyId,
            mockedAccountId,
            requestStateUpdater
        );
    });
});
