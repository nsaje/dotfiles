import {asapScheduler, of} from 'rxjs';
import * as clone from 'clone';
import {tick, fakeAsync} from '@angular/core/testing';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {UsersEndpoint} from './users.endpoint';
import {UsersService} from './users.service';
import {User} from '../types/user';

describe('UsersService', () => {
    let service: UsersService;
    let usersEndpointStub: jasmine.SpyObj<UsersEndpoint>;
    let requestStateUpdater: RequestStateUpdater;

    let mockedUser: User;
    let mockedUsers: User[];
    let mockedCreateUsers: User[];
    let mockedUserId: string;
    let mockedAgencyId: string;
    let mockedAccountId: string;

    beforeEach(() => {
        usersEndpointStub = jasmine.createSpyObj(UsersEndpoint.name, [
            'list',
            'create',
            'validate',
            'get',
            'edit',
            'remove',
        ]);
        service = new UsersService(usersEndpointStub);
        requestStateUpdater = (requestName, requestState) => {};

        mockedAgencyId = '71';
        mockedAccountId = '55';
        mockedUserId = '456346';
        mockedUsers = [
            {
                id: 10000000,
                email: 'test.user@outbrain.com',
                firstName: 'Test',
                lastName: 'User',
                entityPermissions: [
                    {
                        agencyId: mockedAgencyId,
                        permission: 'read',
                    },
                ],
            },
            {
                id: 10000001,
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
            },
            {
                id: 10000002,
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
            },
        ];
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
            .create(mockedCreateUsers, requestStateUpdater)
            .subscribe(user => {
                expect(user).toEqual(mockedUsers);
            });
        tick();

        expect(usersEndpointStub.create).toHaveBeenCalledTimes(1);
        expect(usersEndpointStub.create).toHaveBeenCalledWith(
            mockedCreateUsers,
            requestStateUpdater
        );
    }));

    it('should get user via endpoint', () => {
        usersEndpointStub.get.and
            .returnValue(of(mockedUser, asapScheduler))
            .calls.reset();

        service.get(mockedUserId, requestStateUpdater).subscribe(user => {
            expect(user).toEqual(mockedUser);
        });
        expect(usersEndpointStub.get).toHaveBeenCalledTimes(1);
        expect(usersEndpointStub.get).toHaveBeenCalledWith(
            mockedUserId,
            requestStateUpdater
        );
    });

    it('should edit user via endpoint', () => {
        const mockedNewUser = clone(mockedUsers[0]);
        usersEndpointStub.edit.and
            .returnValue(of(mockedUser, asapScheduler))
            .calls.reset();

        service.edit(mockedNewUser, requestStateUpdater).subscribe(newUser => {
            expect(newUser).toEqual(mockedNewUser);
        });

        expect(usersEndpointStub.edit).toHaveBeenCalledTimes(1);
        expect(usersEndpointStub.edit).toHaveBeenCalledWith(
            mockedNewUser,
            requestStateUpdater
        );
    });

    it('should remove user via endpoint', () => {
        usersEndpointStub.remove.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();

        service.remove(mockedUserId, requestStateUpdater).subscribe(x => {});
        expect(usersEndpointStub.remove).toHaveBeenCalledTimes(1);
        expect(usersEndpointStub.remove).toHaveBeenCalledWith(
            mockedUserId,
            requestStateUpdater
        );
    });

    it('should validate user via endpoint', () => {
        usersEndpointStub.validate.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();

        service.validate(mockedUser, requestStateUpdater).subscribe(x => {});
        expect(usersEndpointStub.validate).toHaveBeenCalledTimes(1);
        expect(usersEndpointStub.validate).toHaveBeenCalledWith(
            mockedUser,
            requestStateUpdater
        );
    });
});
