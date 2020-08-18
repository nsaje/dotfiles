# State management in the users store

This page describes the management of state in the store of the Add/Edit User modal window, specifically of the `activeEntity` attribute.

## Overview
The `activeEntity` attribute in `users.store.state.ts` is defined like this:

```
activeEntity = {
    entity: {
        id: null,
        email: null,
        firstName: null,
        lastName: null,
        entityPermissions: [],
    } as User,
    scopeState: null as ScopeSelectorState,
    entityAccounts: [] as Account[],
    selectedAccounts: [] as Account[],
    selectedEntityPermissions: null as EntityPermissionSelection,
    isReadOnly: null as boolean,
    fieldsErrors: new UsersStoreFieldsErrorsState(),
};
```

The most important attribute here is `entityPermissions`, which contains a list of all entity permissions of a user. An `EntityPermission` is defined like this:
```
export interface EntityPermission {
    agencyId?: string;
    accountId?: string;
    permission: EntityPermissionValue;
}
```
If the entity permission has a set `agencyId`, then it is applied to the whole agency (agency permission, the user is an agency manager).\
If it has a set `accountId`, then it is applied to a particular account (account permission, the user is an account manager).\
If it has neither, it is applied to all agencies and accounts (all accounts permission, the user is an internal user).\
It is not possible for an EntityPermission to have both an `accountId` and an `agencyId`.

If a user has any internal permissions, he can't have any other kind of permission.\
If a user has an agency permission on a particular agency, he can't have account permissions on the same agency.\
If a user has an account permission on a particular agency, he can't have agency permissions on the same agency.



The Add/Edit user form is always used for editing a user's permissions within the scope of a single agency, so it is not possible to deal with a mix of different permissions at the same time. All permissions of a user before and after editing must be of the same type (internal, agency or account permissions). But it is possible to select which type of permissions we wish to have in the Edit user window.



At the time of writing, the Edit user window looks like this:

![Edit user window](https://user-images.githubusercontent.com/36840705/86739388-22a18880-c036-11ea-849c-b74a22f012b3.png)


The various parts of the window are represented by the following store attributes, which are all dependent on `entityPermissions`:
- `scopeState`: Represents the selected level of permissions that a user has: `All accounts`(internal), `Agency`, or `Account`
- `entityAccounts`: A list of all `Account`s, on which the user has any permission, only if `scopeState` is `Account`, otherwise this is an empty list. This list is shown on the left side of the window.
- `selectedAccounts`: A list of all Accounts from the entityAccounts list, which are currently selected for editing, only if scopeState is Account, otherwise this is an empty list. These accounts are coloured orange in the account list.
- `selectedEntityPermissions`: Contains the current state of the checkboxes on the right side of the window. This state is dependent on `entityPermissions` as well as `selectedAccounts` and needs to be updated when the selection of accounts changes.
- `isReadOnly`: This is set to true if the currently logged-in user is not allowed to edit the user displayed in the window. In read-only mode, all window components must be disabled, but it should still be possible to change the selection of accounts on the left side of the window.


The store must support the following operations:
- Load a user and prepare the internal state
- Change the first or last name, or email (only in Add user mode)
- Select a different Access level
- Change selection of accounts (only when Access level is Account)
- Add an account
- Remove account(s)
- Change the selected permissions

Almost all of the changes affect the list of `entityPermissions` in different ways, so i will explain them in more detail below. In each of those changes, the `recalculateActiveEntityState` function is used to recalculate the store's internal state, so i will describe this first.

## recalculateActiveEntityState
This function controls all recalculations of the store's internal variables (scopeState, entityAccounts, selectedAccounts, selectedEntityPermissions and isReadOnly).

Its input parameters are:

- `userPatches: Partial<User>`: This object contains a list of attributes that need to be updated on `activeEntity.entity`. This usually includes an updated list of `entityPermissions`.
- `proposedSelectedAccounts?: Account[]`: This is a list of accounts that we want to select. Whether these will actually be selected depends on some rules defined below.
- `initialize: boolean = false`: Is this the first time this user is being loaded? In that case we need to initialize set up some attributes a bit differently.

At the beginning we create an `activeEntity` object. If the `initialize` parameter is set to true, this is a new object, otherwise it is a copy of the existing one.

The following is a list of helper methods that calculate the internal variables:

### calculateScopeState
This function calculates the value of the `scopeState` attribute. This is done according to the following rules:
- If the user is an internal user, the `scopeState` is `ALL_ACCOUNTS_SCOPE`
- If the user is an agency manager, the `scopeState` is `AGENCY_SCOPE`
- Otherwise, the `scopeState` is `ACCOUNT_SCOPE`

### calculateEntityAccounts
This function calculates the value of the `entityAccounts` attribute:
- Get a distinct list of all `accountId`s that exist in the elements of the `entityPermissions` array
- Map this list of `accountId`s into a list of `Account`s, which are available in `UsersStoreState.accounts`
- Sort the accounts by `id`, so that the displayed list of accounts does not get randomly reordered based on which permission was edited last

### isUserReadOnly
This function calculates the value of the `isReadOnly` attribute:
- If the user is an internal user, we return `true` if the current application user hasn't got a `user` internal permission
- If the user is an agency manager, we return `true` if the current application user hasn't got a `user` internal permission or a `user` agency permission on this agency
- Otherwise, we return `false`

### calculateSelectedAccounts
This function calculates the value of the `selectedAccounts` attribute:

This function accepts the following parameters:
- `activeEntity: UsersStoreState['activeEntity']`: The `activeEntity` that we are currently preparing
- `proposedSelectedAccounts: Account[]`: What we would like the new `selectedAccounts` to be
- `initialize: boolean`: Is this the first time the user is being loaded?

The function's logic is as follows:
- If the selected scopeState is not `ACCOUNT_SCOPE`, return an empty list
- After that:
  - Prepare the variable `selectedAccounts` as an empty array 
  - If initialize is set to false: 
    - If the `proposedSelectedAccounts` function parameter is defined, use this as our value for `selectedAccounts`
    - Else use the existing value for `selectedAccounts` (the selection has not changed)
    - Then remove any accounts from the selection, which are not also a part of the `entityAccounts` array (A use case for this is when we remove a selected account from the list, we do not want it to be selected anymore)
  - After this, if the list of `selectedAccounts` is still empty (Either `initialize` is `true` or the above logic didn't return any accounts), use the default value for `selectedAccounts`, which is determined by the function `getDefaultSelectedAccounts` like this:
    - If the selected `scopeState` is not `ACCOUNT_SCOPE`, OR if the list of `entityAccounts` is empty, return an empty list
    - Else if the user has the same permissions on all accounts, select all accounts in the list of `entityAccounts`
    - Else if an account is selected in the Management console sidebar and the current user has `user` permission on this account, select this account
    - Else select the first account in the list of `entityAccounts`


### getUnknownReportingPermissions
This function gets the list of reporting permissions, whose state is unknown because they are visible on some selected accounts, but not on others.
The result is stored into the variable `unknownReportingPermissions`.
 

### getDisabledReportingPermissions
This function gets the list of reporting permissions which are disabled because the edited user has some higher reporting permissions that the current user can't see.
The exception is that when there are any permissions in the `unknownReportingPermissions` list. In that case, all reporting permissions are disabled.
The result is stored into the variable `disabledReportingPermissions`.


### calculateSelectedEntityPermissions
This function calculates the value of the `selectedEntityPermissions` attribute:

- If the list of `entityPermissions` is empty OR if this user is an account user and no accounts are selected, return an empty object
- Else, assume that the user has the `read` permission, because no matter what level we are editing permissions on, there must at least be a `read` permission
- For every other of the `CONFIGURABLE_PERMISSIONS`, which are currently:
  - `write`
  - `budget`
  - `user`
  - `agency_spend_margin`,
  - `media_cost_data_cost_license_fee`
- ...check if this permission should be selected using the `isPermissionSelected` function, which works like this:
  - If the permission is one of the `unknownReportingPermissions`, return `undefined`
  - If the user is an internal user or agency manager:
    - Return `true` if any `entityPermissions` in the list have this permission, otherwise return `false`
  - Else (if the user is an account manager):
    - Get the list of currently selected account IDs from the `selectedAccounts` list
    - Count the number of all selected accounts
    - Count the number of selected accounts which have this permission
    - If no selected accounts have this permission, return `false`
    - If some, but not all selected accounts have this permission, return `undefined`
    - If all the selected accounts have this permission, return `true`


### calculateCheckboxStates
This function determines, which checkboxes should be enabled and which should be disabled.
- For all general permissions:
  - If the current user has this permission in the current scope: enable the checkbox
  - Else: disable the checkbox
- For all reporting permissions:
  - If the current user hasn't got this permission in the current scope: disable the checkbox
  - Else if the user has this permission only on some accounts of the current scope OR if this permission is one of the `disabledReportingPermissions` or `unknownReportingPermissions`: disable the checkbox
  - Else: hide the checkbox

##
Finally, after calculating all these values, the `recalculateActiveEntityState` function calls `patchState` to save the changes into the store's state.

Based on this definition of the `recalculateActiveEntityState` function, we can now look at how state changes coming from the GUI are handled:

## Load a user and prepare the internal state (setActiveEntity)
- If the entity is a new user (we know this if the user has no `id` yet), AND the list of `entityPermissions` is empty, we get the default list of initial entity permissions from the function `getDefaultEntityPermissions`, which works like this:
  - If an account is selected in the sidebar, return a `read` entity permission for its `accountId`
  - Otherwise if the current application user is an internal user OR agency manager of the current agency AND no account is selected in the sidebar, return a `read` permission for the current `agencyId`
  - Otherwise, return an empty list. Of course this is not possible because an account manager must always have an account selected in the sidebar, but we handle it just in case.
- Otherwise, we call the `cleanUpEntityPermissions` function, which makes sure that the `entityPermissions` contain only a single level of permissions (internal/agency/account). If they contain multiple levels, all permissions below the top level get removed.

Then we assign the `entityPermissions` we got with the above logic to the entity, and use this to call `recalculateActiveEntityState`, with initialize attribute set to true.

## Change the first or last name, or email (changeActiveEntity)
This function is only used for simple changes and just forwards the requested changes of the active entity to the `recalculateActiveEntityState` function.

## Select a different Access level (setActiveEntityScope)
Immediately return without changing anything if the change is not allowed (these possibilities will already be disabled in the UI, but we recheck them just in case):
- The newly selected scope is the same as before
- The calling user is an account manager and wants to set `AGENCY_SCOPE`
- The calling user is an account manager or agency manager and wants to set `ALL_ACCOUNTS_SCOPE`
- If the user is setting `AGENCY_SCOPE`, add a `read` permission for the current `agencyId` to the `entityPermissions`.


If the user is setting `ALL_ACCOUNTS_SCOPE`, add a `read` permission without `agencyId` or `accountId` to the `entityPermissions`.

Otherwise we leave the `entityPermissions` empty for now, the user will still have to choose accounts for the permissions later.

Then we use these `entityPermissions` to call `recalculateActiveEntityState`, which prepares everything else.

## Change selection of accounts (setSelectedAccounts)
Just call the `recalculateActiveEntityState` function without any user changes, but the `proposedSelectedAccounts` parameter set to the accounts we wish to select.

## Add an account (addActiveEntityAccount)
- If the account already exists in `entityPermissions`, return immediately.
- Otherwise, if any accounts are selected, copy the current selection's permissions and add them with this account's `accountId`. If the currently logged user hasn't got some permissions on the new account, those permissions are not copied.
- Otherwise add a `read` permission for this account's `accountId` to the list of `entityPermissions`.

Prepare the `proposedSelectedAccounts` parameter so that the newly added account gets added to the current selection.
Then call `recalculateActiveEntityState` with these `entityPermissions` and `proposedSelectedAccounts`.

## Remove account(s) (removeActiveEntityAccounts)
Remove all `entityPermissions` which contain an `accountId` of any account that we wish to remove and call `recalculateActiveEntityState`.

## Change the selected permissions (updateSelectedEntityPermissions)
- If the state of any disabled or hidden checkboxes changes, throw an error
- If the `scopeState` is `ALL_ACCOUNTS_SCOPE`:
  - For each of the selected permissions (checkbox is checked/true), add this entity permission without `accountId` and `agencyId`
- If the scopeState is `AGENCY_SCOPE`:
  - For each of the selected permissions (checkbox is checked/true), add this entity permission with the `agencyId` of the current agency
- Otherwise:
  - If no accounts are selected, return
  - Otherwise:
    - Store all permissions on accounts that are currently not selected into the variable `permissionsOnDeselectedAccounts` (These are not supposed to be changed, because they are not a part of the selection we are currently editing)
    - Store all permissions with an undefined (indeterminate) checkbox state into the variable `unchangedPermissionsOnSelectedAccounts` (We need to preserve these permissions as they were - they are not the same for every one of the selected accounts and the user did not choose to change them)
    - For each of the selected accounts:
      - For each of the selected permissions (checkbox is checked/true), add this entity permission with `accountId`